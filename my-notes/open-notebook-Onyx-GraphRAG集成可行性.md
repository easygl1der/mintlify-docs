---
title: Onyx GraphRAG 集成可行性分析
description: 在 Onyx 中实现 GraphRAG（知识图谱增强检索）的可行性评估和实施方案
---

# Onyx GraphRAG 集成可行性分析

> 分析时间：2026-04-17
> 数据来源：多 Agent 并行分析

## 一、GraphRAG 简介

**GraphRAG** 是 RAG 的增强版本，通过构建知识图谱来：
- 理解实体之间的关系
- 提供更好的全局推理能力
- 改善复杂多跳查询

### 对比传统 RAG

| 维度 | 传统 RAG | GraphRAG |
|------|----------|----------|
| 检索单元 | 文本块 | 实体 + 关系 |
| 推理能力 | 局部 | 全局 |
| 多跳查询 | 困难 | 自然支持 |
| 上下文理解 | 有限 | 深度 |

## 二、现有 KG 基础设施

Onyx 已经具备丰富的知识图谱基础设施：

### 1. 实体提取管道

**文件位置**：`backend/onyx/kg/extractions/extraction_processing.py:203-589`

```python
def kg_extraction(documents: list[Document]) -> KGPipelineResult:
    """知识图谱提取主函数"""

    # 1. 文档预处理
    processed_docs = preprocess_documents(documents)

    # 2. 隐含实体/关系提取
    implicit_entities = extract_implied_entities(processed_docs)

    # 3. 深度提取（使用 LLM）
    deep_extracted = deep_extract_with_llm(
        processed_docs,
        extraction_prompt=KG_EXTRACTION_PROMPT,
    )

    # 4. 实体消歧和合并
    disambiguated = disambiguate_entities(deep_extracted)

    # 5. 关系分类
    relations = classify_relations(disambiguated)

    return KGPipelineResult(
        entities=disambiguated,
        relations=relations,
    )
```

### 2. Vespa KG 集成

**文件位置**：`backend/onyx/document_index/vespa/kg_interactions.py`

```python
def update_chunks_with_kg(
    chunks: list[Chunk],
    entities: list[Entity],
    relations: list[Relation],
) -> None:
    """更新分块，添加 KG 实体和关系信息"""

    for chunk in chunks:
        # 查找与当前 chunk 相关的实体
        chunk_entities = find_entities_in_chunk(chunk, entities)

        # 查找关联的关系
        chunk_relations = find_relations_for_entities(
            chunk_entities,
            relations,
        )

        # 更新 chunk 元数据
        chunk.metadata.update({
            "kg_entities": [e.name for e in chunk_entities],
            "kg_entity_types": [e.type for e in chunk_entities],
            "kg_relations": [
                {"from": r.source, "to": r.target, "type": r.type}
                for r in chunk_relations
            ],
        })
```

### 3. 知识图谱 Worker

```python
# backend/onyx/background/celery/tasks/kg_processing/
# 处理知识图谱构建和聚类任务
```

## 三、GraphRAG 集成方案

### 方案一：检索增强（推荐）

在现有检索管道中添加图遍历：

```python
# backend/onyx/context/search/retrieval/graph_rag.py

def graph_aware_search(
    query: str,
    filters: SearchFilters,
) -> list[InferenceChunk]:
    """图感知的搜索函数"""

    # 1. 查询理解：提取查询中的实体
    query_entities = extract_entities_from_query(query)

    # 2. 一度扩展：查找相关实体
    expanded_entities = set(query_entities)
    for entity in query_entities:
        # 查找直接关联的实体
        related = kg_lookup_related_entities(entity, depth=1)
        expanded_entities.update(related)

    # 3. 图遍历：扩展检索范围
    graph_context = []
    for entity in expanded_entities:
        # 查找实体周围的上下文
        context = kg_get_local_context(entity, radius=2)
        graph_context.extend(context)

    # 4. 混合检索：图上下文 + 向量搜索
    vector_results = vector_search(query, limit=20)
    graph_results = search_chunks_from_context(graph_context)

    # 5. 融合结果
    combined = rrf_fusion([vector_results, graph_results])

    return combined
```

### 方案二：生成增强

在 LLM 生成阶段添加 KG 上下文：

```python
# backend/onyx/chat/llm_loop.py

def build_system_prompt_with_kg(
    query: str,
    chat_state: ChatStateContainer,
) -> str:
    """构建包含 KG 上下文的系统提示"""

    # 1. 提取查询相关实体
    query_entities = extract_entities_from_query(query)

    # 2. 获取实体详情
    entity_details = []
    for entity_name in query_entities:
        details = kg_get_entity_details(entity_name)
        entity_details.append(details)

    # 3. 获取关系路径
    relation_paths = []
    for i, e1 in enumerate(query_entities):
        for e2 in query_entities[i+1:]:
            paths = kg_find_paths(e1, e2, max_hops=2)
            relation_paths.extend(paths)

    # 4. 构建 KG 上下文
    kg_context = format_kg_context(entity_details, relation_paths)

    # 5. 添加到系统提示
    return f"""
[Knowledge Graph Context]
{kg_context}
---
{original_system_prompt}
"""
```

## 四、集成点分析

### 检索阶段

| 文件 | 集成点 |
|------|--------|
| `search_runner.py` | `_embed_and_hybrid_search()` - 添加图扩展 |
| `chunk_retrieval.py` | 扩展 chunk 元数据查询 |
| `search_tool.py` | 添加图遍历作为额外检索路径 |

### 生成阶段

| 文件 | 集成点 |
|------|--------|
| `llm_loop.py` | `run_llm_loop()` - 添加 KG 上下文 |
| `prompt_utils.py` | `_create_context_files_message()` - 包含 KG 信息 |

### 后处理

| 文件 | 集成点 |
|------|--------|
| `shared_utils/utils.py` | 添加图遍历扩展相关实体 |

## 五、数据结构扩展

### 实体模型

```python
# backend/onyx/db/models.py

@dataclass
class KGEntity:
    id: int
    name: str
    type: str  # PERSON, ORGANIZATION, LOCATION, etc.
    description: Optional[str]
    source_chunk_id: str
    properties: dict
    created_at: datetime
```

### 关系模型

```python
@dataclass
class KGRelation:
    id: int
    source_entity_id: int
    target_entity_id: int
    relation_type: str  # WORKS_AT, LOCATED_IN, etc.
    confidence: float
    source_chunk_id: str
    properties: dict
```

### 查询扩展

```python
@dataclass
class GraphQueryExpansion:
    """图查询扩展结果"""
    original_entities: list[str]
    expanded_entities: list[str]
    relation_paths: list[list[str]]
    graph_context: str  # 格式化的图上下文
```

## 六、实施步骤

### Phase 1：图扩展检索（2-3 天）

```python
# 1. 创建图查询函数
# backend/onyx/kg/graph_query.py

def expand_query_with_graph(query: str) -> GraphQueryExpansion:
    """扩展查询，构建图上下文"""
    # 实体提取
    # 一度扩展
    # 路径查找
    # 上下文格式化
```

### Phase 2：结果融合（1-2 天）

```python
# 2. 修改搜索运行器
# backend/onyx/context/search/retrieval/search_runner.py

def search_with_graph_enhancement(query: str, ...):
    # 向量搜索
    vector_results = vector_search(...)

    # 图扩展搜索
    graph_results = graph_aware_search(...)

    # RRF 融合
    return rrf_fusion([vector_results, graph_results])
```

### Phase 3：生成增强（2-3 天）

```python
# 3. 修改提示构建
# backend/onyx/chat/prompt_utils.py

def construct_message_history(...):
    # 添加 KG 上下文
    kg_context = build_kg_context(query)
    messages.append(SystemMessage(content=kg_context))
```

### Phase 4：优化和测试（2-3 天）

- 图遍历性能优化
- 缓存机制
- 边界情况处理
- 评估指标

## 七、性能优化

### 1. 图缓存

```python
from functools import lru_cache

@lru_cache(maxsize=10000)
def kg_lookup_related_entities(entity: str, depth: int = 1) -> set[str]:
    """实体关联缓存"""
    return _query_kg_database(entity, depth)
```

### 2. 增量更新

```python
# 只对新增/修改的文档进行 KG 更新
def update_kg_incremental(document_id: str) -> None:
    """增量更新知识图谱"""
    # 获取文档关联的实体
    # 只更新相关子图
```

### 3. 异步处理

```python
@shared_task
def process_graph_expansion(query_id: str) -> None:
    """异步图扩展任务"""
    # 不阻塞主检索流程
```

## 八、评估指标

### 检索质量

```python
# 1. 召回率提升
# GraphRAG vs 传统 RAG 在多跳查询上的召回率

# 2. 实体覆盖
# 检索结果中相关实体的覆盖率

# 3. 关系准确性
# 图扩展结果的准确率
```

### 性能指标

```python
# 1. 延迟增加
# GraphRAG vs 传统 RAG 的 P95 延迟

# 2. 吞吐量
# 每秒处理的查询数

# 3. 缓存命中率
# 图查询缓存命中率
```

## 九、风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 延迟增加 | 中 | 异步处理 + 缓存 |
| 图质量依赖 | 高 | 完善 KG 提取管道 |
| 实体消歧 | 中 | 使用 LLM 进行消歧 |
| 扩展性 | 低 | 水平扩展 KG 查询服务 |

## 十、推荐优先级

**🥉 第三优先级实现**

理由：
- 需要更多架构讨论
- 依赖现有 KG 基础设施完善
- 收益验证需要 A/B 测试
- 实施周期较长（2-3 周）

## 十一、未来扩展

### 1. 社区发现
```python
# 基于图的文档聚类
# 发现文档间的隐含关系
```

### 2. 路径推理
```python
# 支持复杂的多跳推理查询
# "A 和 B 之间有什么关联？"
```

### 3. 动态更新
```python
# 实时更新知识图谱
# 订阅文档变更事件
```
