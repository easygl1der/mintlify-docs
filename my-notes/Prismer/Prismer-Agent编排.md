---
title: Prismer Agent 编排
description: OpenClaw 插件系统、6 个 Agent 模板深度分析
---

# Prismer Agent 编排

## OpenClaw 架构

### 概述

**OpenClaw** 是 Prismer 的 Agent 运行时，负责：
1. Agent 生命周期管理
2. 工具注册与调用
3. 多 Provider 支持
4. 插件系统

### 项目结构

```
docker/
├── config/
│   ├── openclaw.json      # 主配置
│   ├── SOUL.md            # Agent 行为准则
│   └── AGENTS.md          # 路由规则
├── plugin/
│   ├── prismer-im/        # IM 桥接插件
│   │   ├── plugin.json
│   │   ├── im_bridge.py
│   │   └── requirements.txt
│   └── prismer-workspace/ # Workspace 工具插件
│       ├── plugin.json
│       ├── tools/
│       │   ├── latex_tools.py
│       │   ├── jupyter_tools.py
│       │   ├── pdf_tools.py
│       │   └── data_tools.py
│       └── requirements.txt
├── scripts/
│   ├── start.sh
│   └── setup.sh
└── Dockerfile
```

## 插件系统

### prismer-im (v0.2.0)

**功能**: 桥接 cloud IM ↔ OpenClaw agent

**核心能力**:
- WebSocket 自动重连
- 消息格式转换
- 会话管理

```python
# im_bridge.py 核心逻辑
class IM Bridge:
    def __init__(self, config: IMConfig):
        self.ws_client = WebSocketClient(config.im_url)
        self.agent_client = OpenClawClient(config.agent_url)
        self.reconnect_strategy = ExponentialBackoff(
            initial_delay=1.0,
            max_delay=30.0,
            multiplier=2.0
        )

    async def connect(self):
        while True:
            try:
                await self.ws_client.connect()
                await self.start_forwarding()
            except WebSocketError as e:
                await self.reconnect_strategy.wait()
```

### prismer-workspace (v0.5.0)

**功能**: 24 个 workspace 工具注册

**工具注册流程**:
```python
# tools/__init__.py
from prismer_workspace import register_tools

def register_tools(agent: OpenClawAgent):
    # LaTeX 工具 (7)
    agent.register_tool('latex_project', latex_project)
    agent.register_tool('latex_project_compile', latex_project_compile)
    agent.register_tool('latex_compile', latex_compile)
    agent.register_tool('latex_preview', latex_preview)
    agent.register_tool('latex_templates', latex_templates)
    agent.register_tool('latex_template_create', latex_template_create)
    agent.register_tool('latex_cleanup', latex_cleanup)

    # Jupyter 工具 (4)
    agent.register_tool('jupyter_execute', jupyter_execute)
    agent.register_tool('jupyter_notebook', jupyter_notebook)
    agent.register_tool('jupyter_update_notebook', jupyter_update_notebook)
    agent.register_tool('jupyter_restart', jupyter_restart)

    # PDF/Research 工具 (5)
    agent.register_tool('load_pdf', load_pdf)
    agent.register_tool('navigate_pdf', navigate_pdf)
    agent.register_tool('get_paper_context', get_paper_context)
    agent.register_tool('arxiv_to_prompt', arxiv_to_prompt)
    agent.register_tool('paper_qa', paper_qa)

    # Data 工具 (4)
    agent.register_tool('data_list', data_list)
    agent.register_tool('data_load', data_load)
    agent.register_tool('data_query', data_query)
    agent.register_tool('data_save', data_save)

    # Code 工具 (2)
    agent.register_tool('code_execute', code_execute)
    agent.register_tool('update_code', update_code)

    # UI/Control 工具 (4)
    agent.register_tool('switch_component', switch_component)
    agent.register_tool('send_ui_directive', send_ui_directive)
    agent.register_tool('get_workspace_state', get_workspace_state)
    agent.register_tool('update_notes', update_notes)
```

## Agent 配置

### openclaw.json

```json
{
  "gateway": {
    "host": "0.0.0.0",
    "port": 18900,
    "protocol": "ws"
  },
  "providers": [
    {
      "name": "kimi",
      "type": "openai-compatible",
      "api_base": "https://api.moonshot.cn/v1",
      "model": "kimi-k2.5",
      "api_key_env": "KIMI_API_KEY"
    },
    {
      "name": "claude",
      "type": "anthropic",
      "model": "claude-sonnet-4-20250514",
      "api_key_env": "ANTHROPIC_API_KEY"
    }
  ],
  "plugins": {
    "im": {
      "enabled": true,
      "path": "./plugin/prismer-im"
    },
    "workspace": {
      "enabled": true,
      "path": "./plugin/prismer-workspace"
    }
  },
  "logging": {
    "level": "INFO",
    "format": "json"
  }
}
```

### SOUL.md (Agent 行为准则)

```markdown
# Prismer Soul

You are **Prismer**, an academic research assistant designed to help researchers
with their daily work.

## Core Principles

1. **Accuracy First**
   - Always verify information before presenting
   - Cite sources for all claims
   - Admit uncertainty when appropriate

2. **Academic Rigor**
   - Follow academic writing standards
   - Use proper citation formats
   - Maintain objectivity

3. **Tool Utilization**
   - Use available tools to enhance productivity
   - Report tool usage transparently
   - Handle tool errors gracefully

## Communication Style

- Be concise but thorough
- Use academic tone when appropriate
- Explain complex concepts clearly
- Ask clarifying questions when needed

## Response Format

When presenting research findings:
1. State the main finding
2. Provide evidence
3. Acknowledge limitations
4. Suggest next steps
```

### AGENTS.md (强制路由规则)

```markdown
# Agent Routing Rules

## Mandatory Tool Usage

Certain tasks MUST use specific tools:

| Task | Required Tools |
|------|----------------|
| Writing to notes | `update_notes` |
| Creating LaTeX projects | `latex_project`, `latex_project_compile` |
| Executing code | `jupyter_execute` |
| Loading research papers | `load_pdf`, `arxiv_to_prompt` |

## Prohibited Patterns

- DO NOT directly output LaTeX code without using `latex_project_create`
- DO NOT skip `update_notes` when modifying notes
- DO NOT execute code without `jupyter_execute`

## Handoff Rules

When a task requires multiple capabilities:
1. Complete current step
2. Use appropriate tool for next step
3. Report progress to user
```

## 6 个 Agent 模板

### 模板定义

| 模板 | 系统提示词摘要 | 专长 |
|------|--------------|------|
| `academic-researcher` | 综合研究能力 | 文献检索、综述写作 |
| `data-scientist` | 数据分析 | 统计、可视化 |
| `mathematician` | 数学证明 | 定理证明、计算 |
| `finance-researcher` | 金融分析 | 报表、预测 |
| `paper-reviewer` | 论文评审 | 质量评估、修改建议 |
| `cs-researcher` | CS 研究 | 算法、系统 |

### 模板示例: mathematician

```python
MATHEMATICIAN_TEMPLATE = """
You are a mathematician assistant named MathAgent.

Your expertise:
- Mathematical proof writing (LaTeX)
- Theorem proving (Lean 4, Coq)
- Symbolic computation
- Numerical analysis

Available tools:
- latex_project: Create LaTeX documents
- latex_compile: Compile to PDF
- prover-server: Formal verification (Lean/Coq/Z3)
- jupyter_execute: Numerical computation

Response style:
- Use LaTeX for all mathematical expressions
- Structure proofs with clear steps
- Include counterexamples when applicable
"""
```

## 工具分类详解

### LaTeX 工具 (7)

| 工具 | 参数 | 返回值 | 示例 |
|------|------|--------|------|
| `latex_project` | name, template | projectId | 创建新项目 |
| `latex_project_compile` | projectId, files[] | pdfBase64 | 编译项目 |
| `latex_compile` | fileId, engine | pdfBase64 | 编译单文件 |
| `latex_preview` | projectId | pdfBase64 | 获取预览 |
| `latex_templates` | — | Template[] | 列出模板 |
| `latex_template_create` | templateId, name | projectId | 从模板创建 |
| `latex_cleanup` | projectId | success | 清理临时文件 |

### Jupyter 工具 (4)

| 工具 | 参数 | 返回值 | 示例 |
|------|------|--------|------|
| `jupyter_execute` | code, kernel? | CellResult | 执行代码 |
| `jupyter_notebook` | notebookId | Notebook | 获取 Notebook |
| `jupyter_update_notebook` | cellId, content | success | 更新单元格 |
| `jupyter_restart` | — | success | 重启内核 |

### PDF/Research 工具 (5)

| 工具 | 参数 | 返回值 | 示例 |
|------|------|--------|------|
| `load_pdf` | url or fileId | PDFDocument | 加载 PDF |
| `navigate_pdf` | pageNum | PageContent | 翻页 |
| `get_paper_context` | question | Context | RAG 查询 |
| `arxiv_to_prompt` | arxivId | ArxivPrompt | 论文转 Prompt |
| `paper_qa` | question, paperId | Answer | 论文问答 |

### Data 工具 (4)

| 工具 | 参数 | 返回值 | 示例 |
|------|------|--------|------|
| `data_list` | — | DataFile[] | 列出数据文件 |
| `data_load` | fileId | DataContent | 加载数据 |
| `data_query` | query | QueryResult | SQL 查询 |
| `data_save` | fileId, content | success | 保存数据 |

### Code 工具 (2)

| 工具 | 参数 | 返回值 | 示例 |
|------|------|--------|------|
| `code_execute` | language, code | Output | 执行代码 |
| `update_code` | fileId, content | success | 更新代码文件 |

### UI/Control 工具 (4)

| 工具 | 参数 | 返回值 | 示例 |
|------|------|--------|------|
| `switch_component` | component | success | 切换组件 |
| `send_ui_directive` | directive | success | 发送指令 |
| `get_workspace_state` | — | State | 获取状态 |
| `update_notes` | content | success | 更新笔记 |

## Provider 配置

### Kimi K2.5

```json
{
  "name": "kimi",
  "model": "kimi-k2.5",
  "provider": "moonshot",
  "config": {
    "temperature": 0.7,
    "max_tokens": 8192,
    "top_p": 0.95
  }
}
```

### Claude Sonnet 4

```json
{
  "name": "claude",
  "model": "claude-sonnet-4-20250514",
  "provider": "anthropic",
  "config": {
    "temperature": 0.7,
    "max_tokens": 8192
  }
}
```

## 工具调用流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     工具调用完整流程                               │
└─────────────────────────────────────────────────────────────────┘

1. Agent 决定调用工具
         │
         ▼
2. OpenClaw 路由到 prismer-workspace
         │
         ▼
3. 工具执行器验证参数
         │
         ▼
4. 执行工具逻辑
         │
         ▼
5. 返回结果 / 发送 Directive
         │
         ├──▶ 同步返回: 直接返回给 Agent
         │
         └──▶ 异步 Directive: 通过 SSE 推送到 Frontend
                   │
                   ▼
            ┌─────────────┐
            │ Directive   │
            │   Queue     │
            └─────────────┘
```

## 错误处理

### 工具错误分类

| 错误类型 | 示例 | 处理策略 |
|----------|------|----------|
| **参数错误** | 缺少必需参数 | 返回错误信息，请求补充 |
| **执行错误** | LaTeX 编译失败 | 返回错误日志 |
| **超时错误** | Jupyter 执行超时 | 返回超时信息 |
| **权限错误** | 无文件访问权限 | 请求权限提升 |

### 重试机制

```python
RETRY_CONFIG = {
    'max_attempts': 3,
    'backoff': {
        'initial': 1.0,
        'max': 10.0,
        'multiplier': 2.0
    },
    'retryable_errors': [
        'TimeoutError',
        'ConnectionError',
        'ServiceUnavailable'
    ]
}
```

## 与其他框架对比

| 特性 | OpenClaw | LangGraph | CrewAI |
|------|----------|-----------|--------|
| **工具注册** | 插件系统 | @tool 装饰器 | @tool 装饰器 |
| **状态管理** | EventEmitter | StateGraph | Crew.process |
| **多 Provider** | 原生支持 | 需自定义 | 有限支持 |
| **Directive 协议** | ✅ | ❌ | ❌ |
| **实时推送** | SSE | 需自定义 | 需自定义 |
