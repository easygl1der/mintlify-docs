---
title: Prismer AI 功能
description: 26 个 Workspace 工具完整列表与 AI 能力分析
---

# Prismer AI 功能

## 26 个 Workspace 工具完整列表

### 工具总览矩阵

| 类别 | 数量 | 工具列表 |
|------|------|----------|
| **LaTeX** | 7 | project, project_compile, compile, preview, templates, template_create, cleanup |
| **Jupyter** | 4 | execute, notebook, update_notebook, restart |
| **PDF/Research** | 5 | load_pdf, navigate_pdf, get_paper_context, arxiv_to_prompt, paper_qa |
| **Data** | 4 | data_list, data_load, data_query, data_save |
| **Code** | 2 | code_execute, update_code |
| **UI/Control** | 4 | switch_component, send_ui_directive, get_workspace_state, update_notes |

---

## LaTeX 工具 (7)

### `latex_project`

**功能**: 创建多文件 LaTeX 项目

```typescript
interface CreateProjectParams {
  name: string;
  template: 'article' | 'article-zh' | 'beamer' | 'ieee';
  description?: string;
}

interface CreateProjectResult {
  projectId: string;
  mainFileId: string;
  createdAt: string;
}
```

**使用示例**:
```
Agent: "创建一个新的论文项目"
Tool: latex_project({ name: "my-paper", template: "article" })
Result: { projectId: "proj-001", mainFileId: "file-001" }
```

### `latex_project_compile`

**功能**: 编译多文件 LaTeX 项目

```typescript
interface CompileProjectParams {
  projectId: string;
  engine: 'pdflatex' | 'xelatex' | 'lualatex';
  options?: {
    passes?: number;      // 编译次数 (交叉引用)
    maxErrors?: number;
  };
}

interface CompileProjectResult {
  projectId: string;
  pdfBase64: string;
  errors: LaTeXError[];
  warnings: number;
  compilationTime: number;  // ms
}
```

### `latex_compile`

**功能**: 单文件编译（自动切换到 latex-editor）

```typescript
interface CompileParams {
  fileId: string;
  engine?: 'pdflatex' | 'xelatex' | 'lualatex';
}

interface CompileResult {
  fileId: string;
  pdfBase64: string;
  log: string;
  errors: string[];
}
```

### `latex_preview`

**功能**: 获取 PDF 预览

```typescript
interface PreviewParams {
  projectId: string;
  page?: number;  // 页码，默认 1
  scale?: number; // 缩放比例，默认 1.0
}

interface PreviewResult {
  projectId: string;
  page: number;
  totalPages: number;
  pdfBase64: string;
  width: number;
  height: number;
}
```

### `latex_templates`

**功能**: 列出可用模板

```typescript
interface ListTemplatesResult {
  templates: {
    id: string;
    name: string;
    description: string;
    thumbnail?: string;  // base64 预览图
  }[];
}
```

### `latex_template_create`

**功能**: 从模板创建项目

```typescript
interface CreateFromTemplateParams {
  templateId: string;
  name: string;
}
```

### `latex_cleanup`

**功能**: 清理临时文件

```typescript
interface CleanupParams {
  projectId: string;
  includeBuildFiles: boolean;  // .aux, .log, .bbl
}

interface CleanupResult {
  projectId: string;
  filesDeleted: number;
  spaceReclaimed: number;  // bytes
}
```

---

## Jupyter 工具 (4)

### `jupyter_execute`

**功能**: 执行代码单元

```typescript
interface ExecuteParams {
  code: string;
  language?: 'python' | 'r' | 'julia';
  timeout?: number;  // ms，默认 30000
  cellId?: string;   // 可选，指定 cell ID
}

interface ExecuteResult {
  cellId: string;
  output: {
    type: 'execute_result' | 'error' | 'stream';
    data: Record<string, string>;  // MIME type → content
    execution: number;
  };
  executionTime: number;
  stdout: string;
  stderr: string;
}
```

**输出类型**:

| type | data 格式 | 示例 |
|------|-----------|------|
| `execute_result` | `{ "text/plain": "..." }` | 表达式结果 |
| `error` | `{ "traceback": [...] }` | 异常信息 |
| `stream` | `{ "stdout": "..." }` | print 输出 |

### `jupyter_notebook`

**功能**: 获取 Notebook 信息

```typescript
interface NotebookParams {
  notebookId: string;
}

interface NotebookResult {
  notebookId: string;
  name: string;
  cells: {
    id: string;
    type: 'code' | 'markdown' | 'raw';
    source: string;
    outputs: CellOutput[];
    metadata: Record<string, any>;
  }[];
  kernel: {
    name: string;
    language: string;
    status: 'busy' | 'idle' | 'dead';
  };
}
```

### `jupyter_update_notebook`

**功能**: 更新单元格内容

```typescript
interface UpdateCellParams {
  notebookId: string;
  cellId: string;
  source?: string;        // 新代码
  metadata?: Record<string, any>;
}

interface UpdateCellResult {
  notebookId: string;
  cellId: string;
  updatedAt: string;
}
```

### `jupyter_restart`

**功能**: 重启内核

```typescript
interface RestartResult {
  success: boolean;
  kernelStatus: 'busy' | 'idle';
}
```

---

## PDF/Research 工具 (5)

### `load_pdf`

**功能**: 加载 PDF 文档

```typescript
interface LoadPDFParams {
  source: {
    type: 'url' | 'fileId' | 'arxiv';
    id: string;  // URL / fileId / arxiv ID
  };
  options?: {
    extractMetadata?: boolean;
    extractImages?: boolean;
  };
}

interface LoadPDFResult {
  documentId: string;
  metadata: {
    title?: string;
    authors?: string[];
    pages: number;
    size: number;  // bytes
  };
  firstPageBase64?: string;
}
```

### `navigate_pdf`

**功能**: 翻页并获取页面内容

```typescript
interface NavigateParams {
  documentId: string;
  page: number;
  options?: {
    extractText?: boolean;
    extractTables?: boolean;
  };
}

interface NavigateResult {
  documentId: string;
  page: number;
  totalPages: number;
  text?: string;
  tables?: {
    page: number;
    bbox: number[];
    content: string;  // CSV 格式
  }[];
}
```

### `get_paper_context`

**功能**: RAG 查询论文内容

```typescript
interface GetContextParams {
  documentId: string;
  question: string;
  maxChunks?: number;  // 默认 5
}

interface GetContextResult {
  documentId: string;
  chunks: {
    text: string;
    page: number;
    relevance: number;  // 0-1
  }[];
  answer?: string;  // 可选的生成答案
}
```

### `arxiv_to_prompt`

**功能**: 将 arXiv 论文转换为 AI 友好的 Prompt 格式

```typescript
interface ArxivToPromptParams {
  arxivId: string;
  format?: 'full' | 'abstract' | 'sections';
}

interface ArxivToPromptResult {
  paperId: string;
  prompt: string;
  metadata: {
    title: string;
    authors: string[];
    abstract: string;
    categories: string[];
  };
}
```

### `paper_qa`

**功能**: 论文问答

```typescript
interface PaperQAParams {
  documentId: string;
  question: string;
  language?: 'en' | 'zh';
}

interface PaperQAResult {
  answer: string;
  sources: {
    page: number;
    text: string;
  }[];
  confidence: number;
}
```

---

## Data 工具 (4)

### `data_list`

**功能**: 列出工作区数据文件

```typescript
interface DataListResult {
  files: {
    id: string;
    name: string;
    type: 'csv' | 'json' | 'xlsx' | 'parquet';
    size: number;
    createdAt: string;
    updatedAt: string;
  }[];
}
```

### `data_load`

**功能**: 加载数据文件

```typescript
interface DataLoadParams {
  fileId: string;
  options?: {
    limit?: number;       // 行数限制
    offset?: number;      // 起始行
    columns?: string[];   // 选择列
  };
}

interface DataLoadResult {
  fileId: string;
  data: {
    columns: string[];
    rows: any[][];
    totalRows: number;
  };
}
```

### `data_query`

**功能**: SQL 查询数据

```typescript
interface DataQueryParams {
  fileId: string;
  query: string;  // SQL 语句
}

interface DataQueryResult {
  fileId: string;
  columns: string[];
  rows: any[][];
  executionTime: number;
}
```

### `data_save`

**功能**: 保存数据到文件

```typescript
interface DataSaveParams {
  fileId?: string;  // 可选，更新现有文件
  name: string;
  type: 'csv' | 'json';
  data: any[][] | object[];
  options?: {
    overwrite?: boolean;
  };
}

interface DataSaveResult {
  fileId: string;
  name: string;
  size: number;
  createdAt: string;
}
```

---

## Code 工具 (2)

### `code_execute`

**功能**: 执行代码（不依赖 Jupyter）

```typescript
interface CodeExecuteParams {
  code: string;
  language: 'python' | 'javascript' | 'bash';
  timeout?: number;
}

interface CodeExecuteResult {
  output: string;
  error?: string;
  exitCode: number;
  executionTime: number;
}
```

### `update_code`

**功能**: 更新代码文件

```typescript
interface UpdateCodeParams {
  fileId?: string;
  path: string;
  content: string;
  language?: string;
}

interface UpdateCodeResult {
  fileId: string;
  path: string;
  updatedAt: string;
}
```

---

## UI/Control 工具 (4)

### `switch_component`

**功能**: 切换工作区组件

```typescript
interface SwitchComponentParams {
  component: 'latex' | 'jupyter' | 'pdf' | 'notes' | 'data';
  context?: Record<string, any>;  // 组件特定上下文
}

interface SwitchComponentResult {
  previous: string;
  current: string;
}
```

### `send_ui_directive`

**功能**: 发送 UI 指令

```typescript
interface SendDirectiveParams {
  directive: {
    type: string;
    payload: any;
  };
}

interface SendDirectiveResult {
  sent: boolean;
  directiveId: string;
}
```

### `get_workspace_state`

**功能**: 获取工作区完整状态

```typescript
interface GetWorkspaceStateResult {
  workspaceId: string;
  components: {
    [key: string]: ComponentState;
  };
  activeComponent: string;
  recentFiles: string[];
  agentStatus: 'idle' | 'thinking' | 'executing';
}
```

### `update_notes`

**功能**: 更新笔记内容

```typescript
interface UpdateNotesParams {
  content: string;
  cursorPosition?: number;
  selection?: {
    start: number;
    end: number;
  };
}

interface UpdateNotesResult {
  updatedAt: string;
  wordCount: number;
}
```

---

## AI 能力详解

### Paper Q&A (论文问答)

**架构**: RAG on PDF

```
┌─────────────────────────────────────────────────────────────┐
│                    Paper Q&A 流程                            │
└─────────────────────────────────────────────────────────────┘

1. 用户提问 "这篇论文的主要贡献是什么？"
         │
         ▼
2. get_paper_context 检索相关片段
   - 分块 (chunk)
   - 向量化
   - 相似度搜索
         │
         ▼
3. 构建 Prompt
   [Context chunks]
   [User question]
         │
         ▼
4. LLM 生成答案
         │
         ▼
5. 返回答案 + 来源引用
```

### Notes AI 建议

**触发时机**:
- 用户在 Notes 编辑时
- 等待超过 3 秒无输入
- Agent 分析上下文

**功能**:
- 续写建议
- 语法修正
- 格式优化

### 数据分析工作流

```
┌─────────────────────────────────────────────────────────────┐
│                   数据分析完整流程                            │
└─────────────────────────────────────────────────────────────┘

data_load
    │
    ├──▶ data_query (SQL 分析)
    │         │
    │         ▼
    │    ┌─────────────────┐
    │    │   AG Grid       │
    │    │  (可视化表格)    │
    │    └─────────────────┘
    │
    └──▶ jupyter_execute (代码分析)
              │
              ▼
         ┌─────────────────┐
         │   Matplotlib    │
         │  (图表生成)      │
         └─────────────────┘
              │
              ▼
         update_gallery
         (展示图表)
```

### Skills 系统

**可用技能**:

| 技能 | 功能 |
|------|------|
| `skill_search` | 搜索可用技能 |
| `skill_info` | 获取技能详情 |
| `skill_install` | 安装技能 |
| `skill_list` | 列出已安装技能 |
| `skill_uninstall` | 卸载技能 |
| `skill_update` | 更新技能 |

**技能格式**:
```json
{
  "name": "data-visualization",
  "version": "1.0.0",
  "description": "高级数据可视化技能",
  "tools": ["matplotlib", "seaborn", "plotly"],
  "prompts": [...]
}
```

---

## 高级 AI 功能使用指南

### 1. 启动 Workspace

```typescript
// 选择 Agent 模板
const templates = workspaceService.getAgentTemplates();
// [ "academic-researcher", "data-scientist", "mathematician", ... ]

// 创建会话
const session = await workspaceService.createSession(
  workspaceId,
  "mathematician"  // 选择数学家模板
);
```

### 2. 与 Agent 聊天

```typescript
// 发送消息
const response = await bridgeAPI.sendMessage({
  workspaceId: "ws-123",
  content: "帮我证明勾股定理",
  context: { component: "latex" }
});

// 响应流
for (const chunk of response.stream) {
  console.log(chunk.content);  // 实时输出
}
```

### 3. Agent Directive 操作

```typescript
// Agent 决定执行 LaTeX 编译
// → 自动发送 LATEX_COMPILE_COMPLETE directive
// → Frontend 自动更新 PDF 预览
```

### 4. Paper 功能

```typescript
// 加载论文
const doc = await tools.load_pdf({
  source: { type: "arxiv", id: "2301.00001" }
});

// 提问
const answer = await tools.paper_qa({
  documentId: doc.documentId,
  question: "这篇论文的创新点是什么？"
});
```

### 5. LaTeX 工作流

```typescript
// Agent 管理多文件项目
await tools.latex_project({
  name: "my-paper",
  template: "article"
});

// Agent 编译
const result = await tools.latex_project_compile({
  projectId: "proj-001",
  engine: "xelatex"  // 中文支持
});
```

### 6. Jupyter 集成

```typescript
// Agent 运行代码
const output = await tools.jupyter_execute({
  code: "import numpy as np; np.sqrt(2)",
  language: "python"
});

// 获取 notebook 状态
const notebook = await tools.jupyter_notebook({
  notebookId: "nb-001"
});
```

### 7. 数据分析

```typescript
// Agent 加载数据
await tools.data_load({
  fileId: "data-001",
  options: { limit: 1000 }
});

// Agent 查询
const result = await tools.data_query({
  fileId: "data-001",
  query: "SELECT AVG(price) FROM products GROUP BY category"
});

// Agent 更新可视化
await tools.send_ui_directive({
  directive: {
    type: "UPDATE_GALLERY",
    payload: { chartType: "bar", dataUrl: "..." }
  }
});
```
