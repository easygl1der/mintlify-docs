---
title: Onyx 笔记生成功能可行性分析
description: 在 Onyx 中实现问答时自动生成笔记的功能设计方案
---

# Onyx 笔记生成功能可行性分析

> 分析时间：2026-04-17
> 数据来源：多 Agent 并行分析

## 一、功能概述

**核心功能**：在用户提问和系统回答的过程中，自动生成结构化的学习笔记。

### 使用场景

```python
# 用户问了一个问题
user_query = "解释一下 RAG 的工作原理"

# 系统回答
answer = rag_system.answer(user_query)

# 同时生成笔记
note = note_generator.create_note(
    question=user_query,
    answer=answer,
    context=retrieved_chunks,
    format="detailed",
)
```

### 笔记格式选项

| 格式 | 描述 | 适用场景 |
|------|------|----------|
| `summary` | 简要总结 | 快速回顾 |
| `detailed` | 详细笔记 | 深度学习 |
| `outline` | 大纲形式 | 梳理结构 |
| `flashcards` | 问答卡片 | 记忆复习 |
| `mindmap` | 思维导图 | 理解关系 |

## 二、现有基础设施

### 1. Chat 保存机制

**文件位置**：`backend/onyx/chat/save_chat.py`

```python
def save_chat_message(
    chat_session_id: int,
    message: ChatMessage,
    db_session: Session,
) -> None:
    """保存聊天消息"""
    db_message = ChatMessageDB(
        chat_session_id=chat_session_id,
        user_role=message.role,
        content=message.content,
        tokens=estimate_tokens(message.content),
    )
    db_session.add(db_message)
    db_session.commit()
```

### 2. Deep Research 报告生成

**文件位置**：`backend/onyx/deep_research/dr_loop.py`

```python
FINAL_REPORT_PROMPT = """
你是一个专业的研究报告撰写助手。
根据以下信息撰写一份详细的研究报告。

研究主题：{topic}
相关文档：{documents}
现有报告结构：{structure}

要求：
1. 结构清晰，层次分明
2. 包含关键发现和洞察
3. 引用相关文档
"""

class DeepResearchLoop:
    async def generate_report(
        self,
        topic: str,
        documents: list[Document],
        structure: ReportStructure,
    ) -> Report:
        """生成研究报告"""
```

### 3. LLM 基础设施

```python
# 已有的 LLM 调用能力
llm_call(prompt, model=..., temperature=..., ...)

# 流式响应
Emitter.stream(content)
```

## 三、功能设计

### 3.1 请求结构

```python
# backend/onyx/chat/note_generation.py

@dataclass
class NoteGenerationRequest:
    """笔记生成请求"""
    source_question: str           # 用户原始问题
    answer: str                    # 系统回答
    retrieved_context: list[InferenceChunk]  # 检索到的上下文
    chat_history: list[ChatMessage]  # 对话历史
    note_format: NoteFormat        # 笔记格式
    target_length: NoteLength      # 目标长度
    include_citations: bool        # 是否包含引用
    language: str = "zh"           # 语言

@dataclass
class NoteFormat(Enum):
    SUMMARY = "summary"           # 简要总结
    DETAILED = "detailed"         # 详细笔记
    OUTLINE = "outline"           # 大纲
    FLASHCARDS = "flashcards"     # 问答卡片
    MINDMAP = "mindmap"           # 思维导图

@dataclass
class NoteLength(Enum):
    SHORT = "short"               # 简短
    MEDIUM = "medium"             # 中等
    LONG = "long"                 # 详细
```

### 3.2 响应结构

```python
@dataclass
class GeneratedNote:
    """生成的笔记"""
    id: str                       # 笔记 ID
    title: str                    # 标题
    content: str                   # 笔记内容（Markdown）
    format: NoteFormat            # 格式
    citations: list[Citation]      # 引用来源
    metadata: NoteMetadata         # 元数据
    created_at: datetime          # 创建时间

@dataclass
class NoteMetadata:
    """笔记元数据"""
    source_question: str
    source_answer: str
    token_count: int
    estimated_read_time: int      # 分钟
    tags: list[str]               # 自动生成的标签
```

### 3.3 提示模板

```python
# backend/onyx/prompts/note_generation.py

SUMMARY_PROMPT = """你是一个专业的学习笔记助手。
根据以下问答内容，生成一份简洁的学习笔记。

## 用户问题
{question}

## 系统回答
{answer}

## 检索上下文
{context}

## 要求
1. 提取关键概念和要点
2. 使用简洁的语言
3. 适当的格式（标题、列表、加粗）
4. 包含相关引用

输出格式：Markdown
语言：{language}
"""

DETAILED_PROMPT = """你是一个专业的学习笔记助手。
根据以下问答内容，生成一份详细的学习笔记。

## 用户问题
{question}

## 系统回答
{answer}

## 检索上下文
{context}

## 要求
1. 详细解释每个关键概念
2. 包含原理说明和示例
3. 添加相关补充知识
4. 使用层级结构（h1, h2, h3）
5. 添加代码示例（如果适用）
6. 包含引用来源

输出格式：Markdown
语言：{language}
"""

OUTLINE_PROMPT = """你是一个专业的学习笔记助手。
根据以下问答内容，生成一份大纲形式的笔记。

## 用户问题
{question}

## 系统回答
{answer}

## 检索上下文
{context}

## 要求
1. 提取主要主题和子主题
2. 使用层级结构
3. 每个点用简短的描述
4. 标记关键概念

输出格式：Markdown 大纲
语言：{language}
"""

FLASHCARDS_PROMPT = """你是一个专业的学习笔记助手。
根据以下问答内容，生成学习卡片。

## 用户问题
{question}

## 系统回答
{answer}

## 检索上下文
{context}

## 要求
1. 提取关键概念
2. 转换为问答对
3. 每张卡片包含：问题、答案、提示

输出格式：Markdown 表格
| 问题 | 答案 | 提示 |
语言：{language}
"""
```

### 3.4 生成流程

```python
# backend/onyx/chat/note_generation.py

class NoteGenerator:
    def __init__(self, llm: LLM):
        self.llm = llm
        self.prompts = {
            NoteFormat.SUMMARY: SUMMARY_PROMPT,
            NoteFormat.DETAILED: DETAILED_PROMPT,
            NoteFormat.OUTLINE: OUTLINE_PROMPT,
            NoteFormat.FLASHCARDS: FLASHCARDS_PROMPT,
        }

    async def generate(
        self,
        request: NoteGenerationRequest,
    ) -> GeneratedNote:
        """生成笔记"""

        # 1. 选择提示模板
        template = self.prompts[request.note_format]

        # 2. 构建上下文
        context = self._build_context(request)

        # 3. 填充模板
        prompt = template.format(
            question=request.source_question,
            answer=request.answer,
            context=context,
            language=request.language,
        )

        # 4. 调用 LLM
        content = await self.llm.call(prompt)

        # 5. 处理引用
        citations = self._extract_citations(request.retrieved_context)

        # 6. 生成元数据
        metadata = NoteMetadata(
            source_question=request.source_question,
            source_answer=request.answer,
            token_count=len(content.split()),
            estimated_read_time=len(content.split()) // 200,
            tags=self._generate_tags(request),
        )

        # 7. 生成标题
        title = self._generate_title(request.source_question)

        return GeneratedNote(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            format=request.note_format,
            citations=citations,
            metadata=metadata,
            created_at=datetime.now(),
        )
```

## 四、集成点

### 4.1 LLM Loop 集成

```python
def run_llm_loop(
    query: str,
    chat_state: ChatStateContainer,
    generate_note: bool = False,
    note_format: NoteFormat = NoteFormat.DETAILED,
) -> Generator[str, None, GeneratedNote]:
    """主 LLM 循环"""

    for turn in range(max_turns):
        # ... 现有逻辑 ...

        if response.tool_calls:
            continue
        else:
            yield from process_final_response(response)

            # 生成笔记（如果请求）
            note = None
            if generate_note:
                note = await note_generator.generate(NoteGenerationRequest(
                    source_question=query,
                    answer=response.content,
                    retrieved_context=chat_state.get_retrieved_chunks(),
                    chat_history=chat_state.history,
                    note_format=note_format,
                    include_citations=True,
                ))

            return note
```

### 4.2 API 端点

```python
# backend/onyx/server/features/notes/api.py

@router.post("/notes/generate")
async def generate_note(
    request: NoteGenerationRequest,
) -> GeneratedNote:
    """从问答生成笔记"""
    generator = NoteGenerator(llm)
    return await generator.generate(request)


@router.get("/notes/{note_id}")
async def get_note(note_id: str) -> GeneratedNote:
    """获取笔记详情"""
    return note_store.get(note_id)


@router.get("/notes/user/{user_id}")
async def list_user_notes(user_id: str) -> list[NoteSummary]:
    """列出用户笔记"""
    return note_store.list_by_user(user_id)


@router.put("/notes/{note_id}")
async def update_note(
    note_id: str,
    updates: NoteUpdateRequest,
) -> GeneratedNote:
    """更新笔记"""
    return note_store.update(note_id, updates)


@router.delete("/notes/{note_id}")
async def delete_note(note_id: str) -> None:
    """删除笔记"""
    note_store.delete(note_id)
```

### 4.3 存储模型

```python
# backend/onyx/db/models.py

class GeneratedNote(Base):
    __tablename__ = "generated_note"

    id: int
    user_id: UUID                    # 所有者
    chat_session_id: Optional[int]    # 关联的聊天会话
    title: str
    content: str                      # Markdown 内容
    format: str                       # 笔记格式
    source_question: str              # 原始问题
    source_answer: str                # 原始回答
    token_count: int
    tags: list[str]                   # JSON 数组
    created_at: datetime
    updated_at: datetime
```

## 五、前端实现

### 5.1 笔记生成按钮

```typescript
// web/src/components/chat/ChatMessage.tsx

interface ChatMessageProps {
  message: Message;
  onGenerateNote?: () => void;
}

function ChatMessage({ message, onGenerateNote }: ChatMessageProps) {
  const [isGeneratingNote, setIsGeneratingNote] = useState(false);

  const handleGenerateNote = async () => {
    setIsGeneratingNote(true);
    try {
      const note = await fetch('/api/notes/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_question: message.relatedQuestion,
          answer: message.content,
          note_format: 'detailed',
        }),
      });
      showNotePreview(note);
    } finally {
      setIsGeneratingNote(false);
    }
  };

  return (
    <div className="message-actions">
      <Button onClick={handleGenerateNote} loading={isGeneratingNote}>
        生成笔记
      </Button>
    </div>
  );
}
```

### 5.2 笔记预览/编辑器

```typescript
// web/src/components/notes/NotePreviewModal.tsx

interface NotePreviewModalProps {
  note: GeneratedNote;
  onSave: () => void;
  onEdit: () => void;
  onClose: () => void;
}

function NotePreviewModal({ note, onSave, onEdit, onClose }: NotePreviewModalProps) {
  return (
    <Modal title="生成笔记" onClose={onClose}>
      <div className="note-preview">
        <h1>{note.title}</h1>
        <div className="markdown-content">
          <MarkdownRenderer content={note.content} />
        </div>
        <div className="citations">
          {note.citations.map((c, i) => (
            <Citation key={i} {...c} />
          ))}
        </div>
      </div>
      <div className="actions">
        <Button onClick={onEdit}>编辑</Button>
        <Button type="primary" onClick={onSave}>保存</Button>
      </div>
    </Modal>
  );
}
```

### 5.3 笔记列表页面

```typescript
// web/src/app/notes/page.tsx

function NotesPage() {
  const { data: notes } = useSWR('/api/notes/user/me', fetcher);

  return (
    <div className="notes-page">
      <header>
        <h1>我的笔记</h1>
        <Button onClick={() => showCreateModal()}>新建笔记</Button>
      </header>
      <div className="notes-grid">
        {notes?.map((note) => (
          <NoteCard key={note.id} note={note} />
        ))}
      </div>
    </div>
  );
}
```

## 六、实施步骤

### Phase 1：核心功能（3-4 天）

```python
# 1. 创建 note_generation.py
# backend/onyx/chat/note_generation.py

# 2. 创建 API 端点
# backend/onyx/server/features/notes/api.py

# 3. 创建数据库模型
# backend/onyx/db/models.py

# 4. 创建提示模板
# backend/onyx/prompts/note_generation.py
```

### Phase 2：UI 集成（2-3 天）

```typescript
// 1. 笔记生成按钮
// web/src/components/chat/ChatMessage.tsx

// 2. 笔记预览模态框
// web/src/components/notes/NotePreviewModal.tsx

// 3. 笔记列表页面
// web/src/app/notes/page.tsx
```

### Phase 3：高级功能（2-3 天）

```python
# 1. 多种格式支持
# 2. 笔记标签和搜索
# 3. 笔记分享功能
```

## 七、优势分析

| 优势 | 说明 |
|------|------|
| **学习效率** | 自动记录关键知识点 |
| **知识沉淀** | 将零散问答转化为结构化笔记 |
| **复习支持** | 多种格式支持复习场景 |
| **引用追溯** | 保留来源，便于深入学习 |

## 八、风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 生成质量 | 中 | 提示工程优化 |
| 延迟增加 | 低 | 异步生成 |
| 存储成本 | 低 | 增量存储 |
| 隐私问题 | 中 | 用户数据隔离 |

## 九、推荐优先级

**🥈 第二优先级实现**

理由：
1. 用户价值高（自动笔记生成）
2. 复用现有 LLM 基础设施
3. 实施难度中等（2 周）
4. 可以独立验证效果

## 十、未来扩展

### 1. 笔记知识库

```python
# 将笔记自动索引到知识库
# 支持笔记间检索
note_indexer.index_note(note)
```

### 2. AI 辅导

```python
# 基于笔记生成练习题
# 错题本功能
quiz_generator.generate_from_notes(note)
```

### 3. 协作笔记

```python
# 多用户协作编辑
# 笔记评论
collaboration.add_comment(note_id, comment)
```
