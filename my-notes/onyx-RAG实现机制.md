---
title: RAG 实现机制
description: Onyx 中 Retrieval-Augmented Generation 的检索和生成机制深度分析
---

# Onyx RAG 实现机制

> 分析时间：2026-04-17
> 数据来源：多 Agent 并行分析

## 一、RAG 架构概览

```
用户查询
    ↓
查询嵌入（Query Embedding）
    ↓
混合搜索（向量 + 关键词）
    ↓
RRF 融合（Reciprocal Rank Fusion）
    ↓
LLM 生成（带引用）
```

## 二、检索阶段

### 搜索运行器

**文件位置**：`backend/onyx/context/search/retrieval/search_runner.py`

```python
def search_chunks(
    query: str,
    filters: SearchFilters,
    hybrid_alpha: float = 0.5,  # 0=纯向量, 1=纯关键词
    limit: int = 20,
    recency_bias: float = 0.0,
) -> list[InferenceChunk]:
    """混合搜索主函数"""

    # 1. 查询嵌入
    query_embedding = get_query_embedding(query)

    # 2. 混合搜索
    if hybrid_alpha < 1.0:
        vector_results = document_index.semantic_search(
            query_embedding=query_embedding,
            filters=filters,
            limit=limit * 2,
        )

    if hybrid_alpha > 0.0:
        keyword_results = document_index.keyword_search(
            query=query,
            filters=filters,
            limit=limit * 2,
        )

    # 3. RRF 融合
    combined = combine_retrieval_results(
        results=[vector_results, keyword_results],
        weights=[1 - hybrid_alpha, hybrid_alpha],
        method="rrf",
    )

    return combined[:limit]
```

### 混合搜索权重

| hybrid_alpha 值 | 搜索模式 |
|----------------|----------|
| 0.0 | 纯语义搜索（向量相似度） |
| 0.5 | 语义 + 关键词各 50% |
| 1.0 | 纯关键词搜索（BM25） |

## 三、搜索工具管道

**文件位置**：`backend/onyx/tools/tool_implementations/search/search_tool.py`

### 多阶段检索流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 查询扩展（并行）                                            │
│    ├── 语义重述（semantic_query_rephrase）                     │
│    ├── 关键词扩展（keyword_query_expansion）                    │
│    └── LLM 生成查询（从聊天历史）                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. 加权 RRF 融合                                             │
│    多个查询结果加权合并                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. 分块合并（Chunk Merging）                                  │
│    合并相邻分块保证答案完整性                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. LLM 文档选择                                              │
│    选择最相关段落进行扩展             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. 上下文扩展（Section Expansion）                             │
│    扩展选定段落周围上下文              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. 最终输出                                                  │
│    构建引用字符串                       │
└─────────────────────────────────────────────────────────────┘
```

### 查询扩展实现

```python
async def expand_query(query: str, chat_history: list[Message]) -> list[ExpandedQuery]:
    tasks = [
        semantic_query_rephrase(query),      # 语义重述
        keyword_query_expansion(query),       # 关键词扩展
        generate_query_from_history(chat_history),  # 历史生成
    ]

    results = await asyncio.gather(*tasks)

    return [
        ExpandedQuery(text=q, weight=w, type=t)
        for q, w, t in zip(results, [0.4, 0.3, 0.3], ["semantic", "keyword", "history"])
    ]
```

### 分块合并策略

```python
def merge_individual_chunks(
    chunks: list[InferenceChunk],
    max_merged_tokens: int = 2000,
) -> list[InferenceSection]:
    """合并相邻分块以保证答案完整性"""

    sections = []
    current_section = []

    for chunk in chunks:
        current_tokens = estimate_tokens(current_section)

        if current_tokens + estimate_tokens([chunk]) <= max_merged_tokens:
            current_section.append(chunk)
        else:
            sections.append(create_section(current_section))
            current_section = [chunk]

    if current_section:
        sections.append(create_section(current_section))

    return sections
```

## 四、生成阶段

### LLM 循环

**文件位置**：`backend/onyx/chat/llm_loop.py`

```python
def run_llm_loop(
    query: str,
    chat_state: ChatStateContainer,
    max_turns: int = 6,
) -> Generator[str, None, None]:
    """主 LLM 循环，最多 6 轮工具调用"""

    for turn in range(max_turns):
        # 1. 构建消息
        messages = construct_message_history(
            query=query,
            chat_state=chat_state,
        )

        # 2. 调用 LLM（带工具）
        response = llm.call_with_tools(
            messages=messages,
            tools=available_tools,
        )

        # 3. 处理响应
        if response.tool_calls:
            tool_results = run_tool_calls(response.tool_calls)
            chat_state.add_message(response)
            chat_state.add_tool_results(tool_results)
            continue
        else:
            yield from process_final_response(response)
            break
```

### 可用工具

| 工具 | 功能 |
|------|------|
| `internal_search` | 内部文档搜索 |
| `FileReaderTool` | 文件读取 |
| `PythonTool` | Python 执行 |
| `WebSearchTool` | 网络搜索 |
| `ImageGenerationTool` | 图像生成 |
| `memory_search` | 记忆搜索 |

## 五、上下文组装

**文件位置**：`backend/onyx/chat/prompt_utils.py`

```python
def construct_message_history(
    query: str,
    chat_state: ChatStateContainer,
) -> list[ChatMessage]:
    """构建完整的消息历史"""

    messages = []

    # 1. 系统提示
    messages.append(SystemMessage(content=build_system_prompt(...)))

    # 2. 自定义 Agent 提示
    if chat_state.agent_prompt:
        messages.append(SystemMessage(content=chat_state.agent_prompt))

    # 3. 上下文文件
    context_files = chat_state.get_context_files()
    if context_files:
        messages.append(_create_context_files_message(context_files))

    # 4. 检索到的文档块
    retrieved_chunks = chat_state.get_retrieved_chunks()
    if retrieved_chunks:
        messages.append(_create_retrieved_docs_message(retrieved_chunks))

    # 5. 聊天历史
    truncated_history = truncate_to_token_budget(
        chat_state.history,
        max_tokens=MAX_CONTEXT_TOKENS,
    )
    messages.extend(truncated_history)

    # 6. 当前查询
    messages.append(UserMessage(content=query))

    return messages
```

## 六、关键数据结构

### InferenceChunk

```python
@dataclass
class InferenceChunk:
    """检索到的文档块"""
    chunk_id: str
    document_id: str
    content: str                    # 文本内容
    score: float                     # 相关性分数
    metadata: dict                  # 元数据
    embedding: list[float]          # 向量
    section_summary: str            # 段落摘要
    content_summary: str            # 内容摘要
```

### InferenceSection

```python
@dataclass
class InferenceSection:
    """分组后的相关分块"""
    combined_content: str           # 合并后的内容
    source_links: list[SourceLink]  # 来源链接
    chunks: list[InferenceChunk]    # 原始分块
    metadata: dict
```

### SearchDoc

```python
@dataclass
class SearchDoc:
    """LLM 面向的文档（用于引用）"""
    link: str                       # 文档链接
    source: str                     # 来源类型
    semantic_identifier: str        # 标题
    metadata: dict                  # 元数据
    content: str                    # 内容
```

## 七、引用处理

**文件位置**：`backend/onyx/chat/citation_processing.py`

```python
def process_citations(
    response: LLMResponse,
    chunks: list[InferenceChunk],
) -> ProcessedResponse:
    """处理生成回复中的引用"""

    # 1. 识别引用标记
    citation_pattern = r"\[(\d+)\]"
    matches = re.finditer(citation_pattern, response.content)

    # 2. 解析引用
    for match in matches:
        chunk_id = int(match.group(1))
        chunk = find_chunk_by_id(chunk_id, chunks)

        citation = Citation(
            number=int(match.group(1)),
            chunk=chunk,
            display_text=create_display_text(chunk),
        )

        response.citations.append(citation)

    return response
```

## 八、检索配置选项

```python
@dataclass
class SearchConfig:
    # 混合搜索权重
    hybrid_alpha: float = 0.5

    # 分块数量限制
    max_chunks: int = 20
    max_chunks_per_section: int = 10

    # 分块合并
    enable_chunkMerging: bool = True
    merged_chunk_tokens: int = 2000

    # 查询扩展
    enable_query_expansion: bool = True
    num_queries: int = 3

    # 时间衰减
    recency_bias: float = 0.0

    # 最小相关分数
    min_score: float = 0.0
```

## 九、关键文件汇总

| 组件 | 文件路径 |
|------|----------|
| 搜索运行器 | `backend/onyx/context/search/retrieval/search_runner.py` |
| 搜索工具 | `backend/onyx/tools/tool_implementations/search/search_tool.py` |
| LLM 循环 | `backend/onyx/chat/llm_loop.py` |
| 聊天处理 | `backend/onyx/chat/process_message.py` |
| 提示构建 | `backend/onyx/chat/prompt_utils.py` |
| 引用处理 | `backend/onyx/chat/citation_processing.py` |
| Vespa 检索 | `backend/onyx/document_index/vespa/chunk_retrieval.py` |
| 上下文 RAG | `backend/onyx/prompts/contextual_retrieval.py` |

## 十、性能优化策略

### 1. 向量缓存

```python
@cache(ttl=3600)
def get_query_embedding(query: str) -> list[float]:
    """查询嵌入缓存（1 小时）"""
    return embedding_model.encode(query)
```

### 2. 批量检索

```python
async def batch_search(queries: list[str]) -> list[list[InferenceChunk]]:
    """批量查询（减少网络往返）"""
    embeddings = await asyncio.gather(*[get_query_embedding(q) for q in queries])
    return await document_index.batch_semantic_search(embeddings, ...)
```

### 3. 分层检索

```python
# 粗排：向量检索 top 100
# 精排：LLM 重排 top 20
def two_stage_retrieval(query: str) -> list[InferenceChunk]:
    # Stage 1: 向量搜索
    candidates = vector_search(query, limit=100)

    # Stage 2: LLM 重排
    reranked = llm_rerank(query, candidates, limit=20)

    return reranked
```
