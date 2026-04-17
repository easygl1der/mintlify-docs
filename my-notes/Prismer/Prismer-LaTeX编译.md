---
title: Prismer LaTeX 编译
description: Docker 服务栈、3 种引擎、模板库深度分析
---

# Prismer LaTeX 编译

## Docker 服务架构

### 服务概览

```
┌──────────────────────────────────────────────────────────────────┐
│                     Container Gateway (:16888)                     │
│                      Node.js 反向代理                              │
│  ┌────────────┬────────────┬────────────┬────────────┐         │
│  │            │            │            │            │         │
│  │  LaTeX     │  Jupyter   │   Prover   │   arXiv    │         │
│  │  :8080     │  :8888     │   :8081    │   :8082   │         │
│  │            │            │            │            │         │
│  └────────────┴────────────┴────────────┴────────────┘         │
│        │              │              │              │           │
└────────┴──────────────┴──────────────┴──────────────┴───────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
    pdflatex/      Jupyter        Lean 4/        arXiv
    xelatex/       Kernel         Coq/Z3         API
    lualatex                                       (8082)
```

### 服务端口映射

| Service | Internal Port | Host Port | Protocol | Purpose |
|---------|--------------|-----------|----------|---------|
| **Gateway** | 3000 | 16888 | HTTP/WS | 反向代理，中央入口 |
| **LaTeX** | 8080 | 18080 | HTTP | 文档编译服务 |
| **Prover** | 8081 | — | HTTP | 形式化验证 |
| **Jupyter** | 8888 | 18888 | HTTP/WS | Notebook kernel |
| **arXiv** | 8082 | — | HTTP | 论文获取 |

### Gateway 反向代理

**设计理念**: 零依赖 Node.js 实现

```typescript
// gateway 核心配置
const routes = [
  { path: '/latex', target: 'http://localhost:8080' },
  { path: '/jupyter', target: 'http://localhost:8888' },
  { path: '/prover', target: 'http://localhost:8081' },
  { path: '/arxiv', target: 'http://localhost:8082' },
];
```

**优势**:
- 零外部依赖
- 统一入口
- 简化客户端配置

## LaTeX 服务深度解析

### 支持的引擎

| 引擎 | 命令 | 用途 |
|------|------|------|
| **pdflatex** | `pdflatex -interaction=nonstopmode` | 标准 PDF 生成 |
| **xelatex** | `xelatex -interaction=nonstopmode` | Unicode + CJK 支持 |
| **lualatex** | `lualatex -interaction=nonstopmode` | Lua 脚本支持 |

### LaTeX 工具链 (26 个中的 7 个)

| 工具 | 函数 | 描述 |
|------|------|------|
| `latex_project` | `createProject()` | 创建多文件 LaTeX 项目 |
| `latex_project_compile` | `compileProject()` | 编译多文件项目 |
| `latex_compile` | `compile()` | 单文件编译 |
| `latex_preview` | `getPreview()` | 获取 PDF 预览 |
| `latex_templates` | `listTemplates()` | 列出模板 |
| `latex_template_create` | `createFromTemplate()` | 从模板创建 |
| `latex_cleanup` | `cleanup()` | 清理临时文件 |

### 编译流程

```
┌─────────────────────────────────────────────────────────────────┐
│                      编译流程                                     │
└─────────────────────────────────────────────────────────────────┘

1. Agent 调用 latex_compile
         │
         ▼
2. POST /latex/compile
   {
     "projectId": "proj-123",
     "mainFile": "main.tex",
     "engine": "pdflatex" | "xelatex" | "lualatex",
     "options": {
       "interaction": "nonstopmode",
       "haltOnError": false
     }
   }
         │
         ▼
3. LaTeX Server 执行编译
   $ pdflatex -interaction=nonstopmode main.tex
         │
         ├──▶ 成功 → 生成 main.pdf
         │
         └──▶ 失败 → 捕获错误日志
                   - Line numbers
                   - Error messages
                   - Warning counts
         │
         ▼
4. 读取 PDF (base64 编码)
   $ base64 main.pdf > main.pdf.b64
         │
         ▼
5. 发送 Directive 到 Frontend
   {
     "type": "LATEX_COMPILE_COMPLETE",
     "payload": {
       "projectId": "proj-123",
       "pdfBase64": "JVBERi0xLjQK...",
       "errors": [],
       "warnings": 3
     }
   }
         │
         ▼
6. Frontend 渲染 PDF
```

### 模板库

| 模板 | 文件 | 适用场景 |
|------|------|----------|
| **article** | `article.cls` | 学术论文 |
| **article-zh** | `ctexart.cls` | 中文论文 |
| **beamer** | `beamer.cls` | 演示文稿 |
| **ieee** | `IEEEtran.cls` | IEEE 期刊 |
| **acmart** | `acmart.cls` | ACM 会议 |
| **svjour** | `svjour3.cls` | Springer 期刊 |

### 模板文件结构

```
templates/
└── article/
    ├── main.tex
    ├── sections/
    │   ├── abstract.tex
    │   ├── introduction.tex
    │   ├── methods.tex
    │   ├── results.tex
    │   └── conclusion.tex
    ├── figures/
    │   └── placeholder.png
    ├── tables/
    │   └── placeholder.tex
    └── references/
        └── refs.bib
```

## Prover 服务 (形式化验证)

### 支持的系统

| 系统 | 语言 | 用途 |
|------|------|------|
| **Lean 4** | Lean | 数学定理证明 |
| **Coq** | Coq | 函数式验证 |
| **Z3** | SMT | 自动化验证 |

### Prover API

```typescript
// /prover/verify
interface VerifyRequest {
  system: 'lean' | 'coq' | 'z3';
  code: string;
  timeout: number;  // ms, 默认 60000
}

interface VerifyResponse {
  success: boolean;
  output: string;
  errors: ProverError[];
  proofSteps: number;
  executionTime: number;
}
```

### prover-server.py

**行数**: ~400 行 (估算)

**核心功能**:
```python
class ProverServer:
    def __init__(self, port=8081):
        self.provers = {
            'lean': LeanProver(),
            'coq': CoqProver(),
            'z3': Z3Prover()
        }
        self.cache = LRUCache(max_size=100)

    def verify(self, system, code, timeout=60):
        # 检查缓存
        cache_key = hash((system, code))
        if cache_key in self.cache:
            return self.cache[cache_key]

        # 执行验证
        result = self.provers[system].verify(code, timeout)

        # 缓存结果
        self.cache[cache_key] = result
        return result
```

## Jupyter 服务

### 集成方式

| 组件 | 说明 |
|------|------|
| **Jupyter Kernel** | Python/R/Julia 代码执行 |
| **Notebook Format** | `.ipynb` 文件格式 |
| **WebSocket** | 实时输出流 |

### Jupyter 工具 (4 个)

| 工具 | 函数 | 描述 |
|------|------|------|
| `jupyter_execute` | `executeCell()` | 执行代码单元 |
| `jupyter_notebook` | `getNotebook()` | 获取 Notebook |
| `jupyter_update_notebook` | `updateCell()` | 更新单元格 |
| `jupyter_restart` | `restartKernel()` | 重启内核 |

### Jupyter Directive

```typescript
// 执行结果
{
  "type": "JUPYTER_CELL_RESULT",
  "payload": {
    "cellId": "cell-001",
    "output": {
      "type": "execute_result",
      "data": { "text/plain": "Hello World" },
      "execution": 1
    },
    "executionTime": 45  // ms
  }
}

// 内核状态
{
  "type": "JUPYTER_KERNEL_BUSY",
  "payload": {
    "busy": false
  }
}
```

## arXiv 服务

### 功能

| 功能 | 描述 |
|------|------|
| **论文获取** | 通过 arXiv ID 获取 PDF |
| **Prompt 转换** | PDF → AI 可处理的 prompt |
| **元数据** | 提取 title, authors, abstract |

### arXiv API

```typescript
// /arxiv/paper
interface ArxivRequest {
  arxivId: string;  // e.g., "2301.00001"
}

interface ArxivResponse {
  paperId: string;
  title: string;
  authors: string[];
  abstract: string;
  pdfUrl: string;
  categories: string[];
  published: string;
}
```

### arxiv-server.py

**核心流程**:
```python
class ArxivServer:
    def __init__(self, port=8082):
        self.arxiv_client = ArxivClient()

    def get_paper(self, arxiv_id: str) -> dict:
        # 1. 获取元数据
        metadata = self.arxiv_client.get_metadata(arxiv_id)

        # 2. 转换为 prompt 格式
        prompt = self._to_prompt(metadata)

        return {
            'metadata': metadata,
            'prompt': prompt
        }

    def _to_prompt(self, metadata: dict) -> str:
        # 构建 AI 友好的 prompt
        template = """
# {title}

## Authors
{authors}

## Abstract
{abstract}

## Categories
{categories}
"""
        return template.format(**metadata)
```

## Python CLI 工具详解

### latex-server.py (505 行)

**命令接口**:
```bash
latex-server.py compile <file.tex> [--engine pdflatex|xelatex|lualatex]
latex-server.py preview <project_id>
latex-server.py templates list
latex-server.py templates create <name> [--template article]
```

**核心模块**:
```python
class LaTeXServer:
    def __init__(self, port=8080):
        self.projects = ProjectManager()
        self.engines = {
            'pdflatex': PDFLaTeXEngine(),
            'xelatex': XeLaTeXEngine(),
            'lualatex': LuaLaTeXEngine()
        }

    def compile(self, file_path: str, engine: str) -> CompileResult:
        # 1. 验证文件存在
        # 2. 执行编译
        result = self.engines[engine].run(file_path)
        # 3. 捕获错误
        # 4. 返回结果
        return result

    def preview(self, project_id: str) -> str:
        # 返回 PDF base64
        pdf_path = self.projects.get_main_pdf(project_id)
        return self._read_base64(pdf_path)
```

### 文件处理流程

```
┌──────────────────────────────────────────────────────────────┐
│                     LaTeX 文件处理流程                          │
└──────────────────────────────────────────────────────────────┘

上传文件
    │
    ▼
┌─────────────┐
│ .tex 文件    │ ──▶ 语法检查
└─────────────┘
    │
    ▼
┌─────────────┐
│ 编译循环     │ ◀──▶ 错误修复循环
└─────────────┘
    │
    ├──▶ 成功 ──▶ PDF 生成
    │
    └──▶ 失败 ──▶ 错误信息反馈
                    - 行号
                    - 错误类型
                    - 修复建议
```

### 常见错误处理

| 错误类型 | LaTeX 错误码 | 修复建议 |
|----------|--------------|----------|
| 缺失包 | `! LaTeX Error: File 'xxx.sty' not found.` | 自动安装或提示 |
| 格式错误 | `! You can't use \...' in horizontal mode.` | 检查对齐 |
| 内存不足 | `! TeX memory overflow` | 分割文档 |
| 编码问题 | `Unicode character` | 使用 xelatex |

## 性能与缓存

### 编译缓存

```typescript
interface CompileCache {
  key: string;        // hash(file_content + engine + options)
  result: CompileResult;
  timestamp: number;
  ttl: number;        // 5 minutes
}
```

### 并发控制

| 限制 | 值 | 说明 |
|------|-----|------|
| 最大并发编译 | 3 | 避免资源竞争 |
| 单个编译超时 | 120s | 防止死循环 |
| 文件大小限制 | 50MB | 防止过大文档 |

## 集成到 Agent 工作流

```typescript
// Agent 调用示例
const agentWorkflow = `
1. Agent 分析用户请求
2. 判断需要 LaTeX 编译
3. 调用 latex_project_compile
4. 接收 LATEX_COMPILE_COMPLETE directive
5. 调用 latex_preview 获取 PDF
6. 展示给用户
`;
```
