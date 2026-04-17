---
title: 文件处理流程
description: Onyx 中 PDF、PPTX 等文件从上传到索引的完整处理流程深度分析
---

# Onyx 文件处理流程

> 分析时间：2026-04-17
> 数据来源：多 Agent 并行分析

## 一、整体处理链路

```
用户上传文件
    ↓
API 接收（POST /user/projects/file/upload）
    ↓
文件存储（file_store.save_file）
    ↓
创建 UserFile 记录（status=PROCESSING）
    ↓
Celery 任务入队（PROCESS_SINGLE_USER_FILE）
    ↓
Docfetching Worker（获取文档）
    ↓
Docprocessing Worker（处理管道）
    ↓
文本提取 → 分块 → 嵌入 → Vespa 索引
    ↓
更新 UserFile.status = COMPLETED
```

## 二、上传入口

**文件位置**：`backend/onyx/server/features/projects/api.py:127`

```python
@router.post("/user/projects/file/upload")
def upload_user_files(...) -> list[UserFileSnapshot]:
    return upload_files_to_user_files_with_indexing(
        project_id=project_id,
        files=files,
        file_names=file_names,
        folder_name=folder_name,
        odes=odes,
        db_session=db,
        user=user,
    )
```

### 上游函数
**文件位置**：`backend/onyx/db/projects.py:119`

```python
def upload_files_to_user_files_with_indexing(...) -> list[UserFile]:
    # 1. 保存文件到存储
    file_ids = file_store.save_file(files, file_names, user_id)

    # 2. 创建 UserFile 记录
    user_files = create_user_files(
        file_ids=file_ids,
        file_names=file_names,
        user_id=user_id,
        project_id=project_id,
        db_session=db_session,
    )

    # 3. 入队 Celery 任务
    for uf in user_files:
        process_single_user_file.apply_async(
            kwargs={"file_id": uf.id, ...},
            expires=...,
        )

    return user_files
```

## 三、Celery Worker 处理

**文件位置**：`backend/onyx/background/celery/tasks/user_file_processing/tasks.py:545`

### 主处理函数

```python
@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_single_user_file(self, file_id: int, ...) -> None:
    # 1. 加载文件
    connector = LocalFileConnector.from_ids(
        source_document_id=file_id,
        source_type=SourceType.FILE,
    )

    # 2. 检查是否需要索引
    if not is_indexing_enabled():
        # 仅提取文本，存储为纯文本
        extract_and_store_plaintext(connector)
        return

    # 3. 执行完整索引管道
    _process_user_file_with_indexing(connector, file_id, db_session)
```

### 非索引模式
- 提取文本内容
- 计算 token 数量
- 存储纯文本到 `UserFile.plaintext`
- 标记状态为 COMPLETED

### 索引模式
- 调用完整索引管道
- 生成向量嵌入
- 存入 Vespa

## 四、文本提取模块

**文件位置**：`backend/onyx/file_processing/extract_file_text.py`

### 支持的文件类型

| 文件类型 | 提取方法 | 库 |
|----------|----------|-----|
| PDF | `read_pdf_file()` | `pypdf.PdfReader` |
| PPTX | `pptx_to_text()` | `markitdown.MarkItDown` |
| DOCX | `read_docx_file()` | `markitdown` |
| XLSX | `xlsx_to_text()` | `openpyxl` |
| 纯文本 | `read_text_file()` | `chardet`（编码检测） |
| EML | `eml_to_text()` | Python email parser |
| EPUB | `epub_to_text()` | ZIP + XHTML 解析 |

### PDF 提取详情

```python
def read_pdf_file(file_path: str) -> ExtractionResult:
    reader = PdfReader(file_path)

    # 提取文本
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"

    # 可选：提取图片
    images = []
    if get_image_extraction_and_analysis_enabled():
        images = extract_images_from_pdf(file_path)

    return ExtractionResult(
        text_content=text,
        embedded_images=images,
        metadata={
            "title": reader.metadata.title,
            "author": reader.metadata.author,
            "pages": len(reader.pages),
        }
    )
```

### PPTX 提取详情

```python
def pptx_to_text(file_path: str) -> str:
    converter = MarkItDown()
    result = converter.convert(file_path)
    return result.text_content
```

### 主入口函数

```python
def extract_text_and_images(
    file_path: str,
    file_name: str,
    ignore_unsupported_file_types: bool = False,
) -> ExtractionResult:
    """主提取函数，根据文件扩展名分发到对应提取器"""

    extension = Path(file_name).suffix.lower()

    if extension == ".pdf":
        return read_pdf_file(file_path)
    elif extension == ".pptx":
        return ExtractionResult(pptx_to_text(file_path), [], {})
    elif extension == ".docx":
        return read_docx_file(file_path)
    # ... 其他类型
```

## 五、索引管道

**文件位置**：`backend/onyx/indexing/indexing_pipeline.py:1099`

### run_indexing_pipeline()

```python
def run_indexing_pipeline(
    document_ids: list[str],
    index_attempt: IndexAttempt,
    db_session: Session,
    ) -> IndexingPipelineResult:
    """
    主索引管道函数
    """
    # 1. 获取文档
    docs = fetch_documents(document_ids, index_attempt, db_session)

    # 2. 文本提取
    docs = batch_extract_text(docs)

    # 3. 分块（Chunking）
    chunks = chunk_documents(docs, index_attempt.chunking_config)

    # 4. 可选：上下文 RAG（添加摘要）
    if index_attempt.enable_contextual_rag:
        chunks = add_contextual_summaries(chunks)

    # 5. 嵌入向量生成
    chunks = generate_embeddings(chunks)

    # 6. 写入 Vespa
    write_chunks_to_vector_db(chunks)

    return IndexingPipelineResult(success=True, ...)
```

### 分块配置

```python
# 使用 SentenceChunker from chonkie
from chonkie import SentenceChunker

chunker = SentenceChunker(
    chunk_token_limit=DOC_EMBEDDING_CONTEXT_SIZE,  # 默认 8192 tokens
    overlap_percentage=0.2,  # 20% 重叠
)

chunks = chunker.chunk(document.text)
```

### 上下文 RAG（可选）

```python
def add_contextual_summaries(chunks: list[Chunk]) -> list[Chunk]:
    """为每个 chunk 添加文档级和块级摘要"""

    # 文档级摘要
    doc_summary = llm_call(DOCUMENT_SUMMARY_PROMPT.format(
        document=document.text
    ))

    # 块级上下文
    for chunk in chunks:
        chunk.context = llm_call(CONTEXTUAL_RAG_PROMPT.format(
            chunk=chunk.text,
            document_summary=doc_summary
        ))

    return chunks
```

## 六、Vespa 索引

**文件位置**：`backend/onyx/document_index/vespa/vespa_document_index.py`

### 写入流程

```python
def write_chunks(chunks: list[Chunk]) -> None:
    # 1. 构建 Vespa 文档
    vespa_docs = [
        {
            "id": chunk.id,
            "fields": {
                "content": chunk.text,
                "embedding": chunk.embedding,
                "metadata": chunk.metadata,
                "context": chunk.context,
            }
        }
        for chunk in chunks
    ]

    # 2. 批量写入
    client.feed_batch(vespa_docs)
```

## 七、后处理钩子

**文件位置**：`backend/onyx/indexing/adapters/user_file_indexing_adapter.py`

### UserFileIndexingAdapter

```python
class UserFileIndexingAdapter(IndexingAdapter):
    def on_index_success(self, document_id: str) -> None:
        # 1. 更新 UserFile 状态
        user_file = db.query(UserFile).filter_by(id=document_id).first()
        user_file.status = UserFileStatus.SUCCESS

        # 2. 存储纯文本
        store_user_file_plaintext(user_file, document.plaintext)

        # 3. 通知所有者
        notify_user_file_ready(user_file)

    def on_index_failure(self, document_id: str, error: str) -> None:
        user_file = db.query(UserFile).filter_by(id=document_id).first()
        user_file.status = UserFileStatus.FAILED
        user_file.error_message = error
```

## 八、文件状态流转

```
CREATE → PROCESSING → SUCCESS
                    ↘ FAILED
```

| 状态 | 说明 |
|------|------|
| `PROCESSING` | 任务已入队，正在处理 |
| `SUCCESS` | 成功完成，已索引 |
| `FAILED` | 处理失败，记录错误信息 |

## 九、前端轮询机制

```typescript
// ProjectsContext.tsx
const usePollingFileStatus = (projectId: number) => {
  const { data: files } = useSWR(
    `/api/user/projects/files/${projectId}`,
    fetcher,
    {
      revalidateInterval: 2000,  // 2 秒轮询
      shouldRetryOnError: false,
    }
  );

  // 检查是否有文件仍在处理
  const isProcessing = files?.some(
    (f: UserFile) => f.status === 'PROCESSING'
  );

  return { files, isProcessing };
};
```

## 十、关键文件汇总

| 组件 | 文件路径 |
|------|----------|
| 上传 API | `backend/onyx/server/features/projects/api.py` |
| 文件创建 | `backend/onyx/db/projects.py` |
| Worker 任务 | `backend/onyx/background/celery/tasks/user_file_processing/tasks.py` |
| 文本提取 | `backend/onyx/file_processing/extract_file_text.py` |
| 索引管道 | `backend/onyx/indexing/indexing_pipeline.py` |
| 分块器 | `backend/onyx/indexing/chunker.py` |
| Vespa 索引 | `backend/onyx/document_index/vespa/vespa_document_index.py` |
| 后处理 | `backend/onyx/indexing/adapters/user_file_indexing_adapter.py` |
| 前端上下文 | `web/src/providers/ProjectsContext.tsx` |
