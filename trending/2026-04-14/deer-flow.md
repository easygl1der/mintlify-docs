

# deer-flow 技术调研报告

> 作者: @bytedance | 今日新增: ⭐+0 | 总计: ⭐0

---

## 基本信息

| 属性 | 值 |
|------|-----|
| **仓库全名** | bytedance/deer-flow |
| **项目描述** | An open-source long-horizon SuperAgent harness that researches, codes, and creates |
| **主要语言** | Python (后端) + TypeScript (前端) |
| **许可证** | MIT License |
| **Star 数** | 58,497 ⭐ |
| **Fork 数** | 7,323 |
| **开放 Issues** | 500+ |
| **创建时间** | 2025-05-07 |
| **最后更新** | 2026-04-06 |
| **官网** | https://deerflow.tech |

### 项目标签 (Topics)

```
agent, agentic, agentic-framework, agentic-workflow, ai, ai-agents, 
deep-research, harness, langchain, langgraph, langmanus, llm, 
multi-agent, nodejs, podcast, python, superagent, typescript
```

---

## 项目简介

DeerFlow 是由字节跳动（ByteDance）开源的 **AI Super Agent Harness（超级智能体运行框架）**，旨在为复杂任务的自动化执行提供完整的基础设施支持。

### 核心定位

DeerFlow 从 Deep Research 框架演进而来，提供智能体运行所需的一切基础设施：

- **文件系统访问**：完整的文件系统读写能力
- **记忆系统**：会话内上下文压缩与跨会话长期记忆
- **技能扩展**：基于 Markdown 的技能定义系统
- **沙箱执行**：隔离的任务执行环境
- **子智能体**：复杂任务的智能分解与并行执行
- **消息网关**：多渠道 IM 集成支持

### 核心特性

| 特性 | 说明 |
|------|------|
| **Sub-Agents** | 复杂任务分解为子任务并行执行，隔离上下文防止干扰 |
| **Sandbox & File System** | 每个任务独立执行环境，支持文件读写、图像查看、Shell 命令 |
| **Context Engineering** | 子智能体独立上下文、会话内压缩、中间结果持久化 |
| **Long-Term Memory** | 跨会话记忆、用户偏好学习、本地存储控制、去重机制 |
| **Skills & Tools** | Markdown 格式技能定义、内置多种技能、MCP 服务器支持 |

### 版本说明

> ⚠️ **重要**：DeerFlow 2.0 是从零重写的版本，与 1.x 版本没有共享代码。1.x 版本仍在 `main-1.x` 分支维护。

---

## 技术栈分析

### 后端技术栈 (Python)

#### 核心框架层

| 组件 | 技术选型 | 版本要求 | 说明 |
|------|----------|----------|------|
| **Web 框架** | FastAPI | ≥ 0.115.0 | 异步 API 框架，类型安全，自动 OpenAPI 文档 |
| **ASGI 服务器** | Uvicorn | ≥ 0.34.0 | 高性能 ASGI 服务器，支持 workers |
| **AI 编排框架** | LangGraph SDK | ≥ 0.1.51 | 基于图的智能体编排，状态管理能力强 |
| **Python 版本** | Python | ≥ 3.12 | 现代化 Python 特性支持 |
| **包管理器** | uv | 最新 | 现代化 Python 包管理工具，比 pip/poetry 更快 |

#### 通信与协议层

| 组件 | 技术选型 | 版本 | 说明 |
|------|----------|------|------|
| **HTTP 客户端** | httpx | ≥ 0.28.0 | 异步 HTTP 客户端，支持 HTTP/2 |
| **文件上传** | python-multipart | ≥ 0.0.20 | FastAPI 表单数据处理 |
| **实时通信** | sse-starlette | ≥ 2.1.0 | Server-Sent Events 支持 |
| **Markdown 转换** | markdown-to-mrkdwn | - | Slack 格式转换 |

#### IM 渠道集成层

| 渠道 | SDK | 版本要求 | 集成复杂度 |
|------|-----|----------|------------|
| **飞书** | lark-oapi | ≥ 1.4.0 | 高 |
| **Slack** | slack-sdk | ≥ 3.33.0 | 中 |
| **Telegram** | python-telegram-bot | ≥ 21.0 | 低 |
| **企业微信** | wecom-aibot-python-sdk | ≥ 0.1.6 | 中 |

### 前端技术栈 (TypeScript/React)

#### 核心框架层

| 组件 | 技术选型 | 版本 | 说明 |
|------|----------|------|------|
| **框架** | Next.js | 16.1.7 | App Router，React 19 |
| **语言** | TypeScript | 5.8.2 | 强类型保障 |
| **包管理器** | pnpm | 10.26.2 | 高性能 monorepo 支持 |
| **运行时** | Node.js | ≥ 22 | 前端构建环境 |

#### UI 与样式层

| 组件 | 技术选型 | 版本 | 说明 |
|------|----------|------|------|
| **CSS 框架** | Tailwind CSS | 4.0.15 | 原子化 CSS，快速样式开发 |
| **UI 组件库** | shadcn/ui + Radix UI | - | 可定制化设计系统 |
| **Toast 通知** | sonner | ≥ 2.0.7 | 轻量级通知组件 |
| **动画库** | GSAP + motion | 3.13.0 / 12.26.2 | 复杂交互动画 |

#### AI 集成层

| 组件 | 技术选型 | 版本 | 用途 |
|------|----------|------|------|
| **AI SDK** | Vercel AI SDK | ≥ 6.0.33 | 流式响应，AI UI 组件 |
| **LangChain 前端** | @langchain/langgraph-sdk | ≥ 1.5.3 | 与后端 LangGraph 通信 |
| **状态管理** | TanStack React Query | - | 服务端状态缓存 |

#### 高级组件层

| 组件 | 技术选型 | 版本 | 用途 |
|------|----------|------|------|
| **流程图可视化** | @xyflow/react | ≥ 12.10.0 | 智能体工作流可视化 |
| **代码编辑器** | @uiw/react-codemirror | ≥ 4.25.4 | 代码展示与编辑 |
| **表单验证** | zod | ≥ 3.24.2 | Schema 验证 |

### 技术架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │
│  │   AI SDK    │  │  xyflow     │  │  CodeMirror │  │  Radix   │  │
│  │   (Vercel)  │  │  (流程图)    │  │  (代码编辑)  │  │  (UI)    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────┘  │
│                              │                                     │
│                     ┌────────▼────────┐                          │
│                     │  TanStack Query │                          │
│                     └────────┬────────┘                          │
└──────────────────────────────┼──────────────────────────────────┘
                               │ HTTP/WebSocket
┌──────────────────────────────▼──────────────────────────────────┐
│                      Gateway API (FastAPI)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │
│  │   SSE       │  │  IM Bridge  │  │  File API   │  │  Auth    │  │
│  │   Handler   │  │  (多渠道)    │  │  Upload     │  │  Gateway │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────┘  │
│                              │                                     │
│                     ┌────────▼────────┐                          │
│                     │   LangGraph     │                          │
│                     │   SDK Client     │                          │
│                     └────────┬────────┘                          │
└──────────────────────────────┼──────────────────────────────────┘
                               │ LangGraph Protocol
┌──────────────────────────────▼──────────────────────────────────┐
│                     LangGraph Server                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │
│  │   Agent     │  │   Memory    │  │   Tools     │  │  Skills   │  │
│  │   Graph     │  │   System    │  │   Executor  │  │  Loader   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────┘  │
│                              │                                     │
│                     ┌────────▼────────┐                          │
│                     │   Sandbox       │                          │
│                     │   Provider      │                          │
│                     └─────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 代码结构

### 仓库根目录结构

```
deer-flow/
├── .dockerignore                    # Docker 构建排除规则
├── .env.example                     # 环境变量模板 (1,310 bytes)
├── .gitattributes                  # Git 属性配置
├── .gitignore                       # Git 忽略规则
├── .github/                         # GitHub Actions 工作流
├── CONTRIBUTING.md                 # 贡献指南 (9,354 bytes)
├── Install.md                       # 安装说明 (4,706 bytes)
├── LICENSE                          # MIT 许可证
├── Makefile                         # 构建自动化 (7,911 bytes)
├── README.md                        # 英文 README (36,688 bytes)
├── README_zh.md                     # 中文 README
├── README_fr.md / README_ja.md / README_ru.md  # 多语言文档
├── SECURITY.md                      # 安全公告
├── backend/                         # Python 后端目录
│   ├── packages/
│   │   └── harness/                 # 核心智能体框架 (可独立发布)
│   │       └── deerflow/
│   │           ├── client.py       # Python 客户端 SDK
│   │           ├── models/          # 模型提供者
│   │           │   ├── vllm_provider.py
│   │           │   ├── claude_provider.py
│   │           │   └── openai_codex_provider.py
│   │           └── ...
│   └── tests/
├── config.example.yaml              # 配置示例 (29,368 bytes)
├── deer-flow.code-workspace         # VS Code 工作区配置
├── docker/                          # Docker 配置目录
│   ├── Dockerfile                   # 多阶段构建
│   └── docker-compose.yaml          # 服务编排
├── docs/                            # 文档目录
│   ├── CONFIGURATION.md
│   ├── MCP_SERVER.md
│   └── MEMORY_SETTINGS_REVIEW.md
├── extensions_config.example.json   # 扩展配置示例
├── frontend/                        # TypeScript 前端目录
│   ├── app/                         # Next.js App Router
│   ├── components/                  # React 组件
│   ├── lib/                         # 工具函数
│   └── package.json
├── scripts/                         # 自动化脚本目录
└── skills/                          # 技能模块目录
    ├── public/                      # 内置技能
    │   ├── research/
    │   ├── report-generation/
    │   ├── slide-creation/
    │   ├── web-page/
    │   ├── image-generation/
    │   ├── video-generation/
    │   └── claude-to-deerflow/
    └── custom/                      # 用户自定义技能
```

### 前后端分离架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Gateway API   │────▶│  LangGraph      │
│   (Next.js)     │     │   (FastAPI)     │     │  Server         │
│   Port: 2026    │     │   Port: 8001    │     │  Port: 2024     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │   Sandbox       │
                                               │   Environment   │
                                               │   (Docker/K8s)   │
                                               └─────────────────┘
```

### 主要文件规模

| 文件/目录 | 规模 | 说明 |
|-----------|------|------|
| README.md | 36,688 bytes | 详尽的使用文档 (~10K 行文本) |
| config.example.yaml | 29,368 bytes | 全面的配置模板 (~700 行) |
| CONTRIBUTING.md | 9,354 bytes | 贡献指南 |
| Makefile | 7,911 bytes | 构建脚本 (~300 行) |
| .env.example | 1,310 bytes | 环境变量模板 |
| extensions_config.example.json | 954 bytes | 扩展配置示例 |

### 代码行数估算

| 组件 | 估算行数 | 说明 |
|------|----------|------|
| **后端核心 (packages/harness)** | ~5,000-8,000 行 | 核心智能体逻辑 |
| **Gateway API** | ~2,000-3,000 行 | FastAPI 路由和业务 |
| **前端应用** | ~8,000-12,000 行 | Next.js 页面和组件 |
| **技能定义 (Markdown)** | ~2,000-3,000 行 | 各技能工作流定义 |
| **配置与脚本** | ~2,000 行 | Makefile、脚本等 |
| **总计** | **~20,000-30,000 行** | 中等规模项目 |

---

## 依赖分析

### 后端核心依赖 (pyproject.toml)

```toml
[project]
name = "deer-flow"
version = "0.1.0"
requires-python = ">=3.12"

dependencies = [
    # === 核心框架 ===
    "deerflow-harness",           # Workspace 核心包
    "fastapi>=0.115.0",           # Web 框架
    "uvicorn[standard]>=0.34.0", # ASGI 服务器
    
    # === 网络通信 ===
    "httpx>=0.28.0",             # 异步 HTTP 客户端
    "python-multipart>=0.0.20",  # 表单数据
    "sse-starlette>=2.1.0",      # SSE 支持
    
    # === AI 集成 ===
    "langgraph-sdk>=0.1.51",     # LangGraph 客户端
    
    # === IM 渠道 ===
    "lark-oapi>=1.4.0",          # 飞书
    "slack-sdk>=3.33.0",         # Slack
    "python-telegram-bot>=21.0", # Telegram
    "wecom-aibot-python-sdk>=0.1.6", # 企业微信
    
    # === 工具库 ===
    "markdown-to-mrkdwn>=0.3.1", # 格式转换
]

[dependency-groups]
dev = ["pytest>=8.0.0", "ruff>=0.14.11"]

[tool.uv.workspace]
members = ["packages/harness"]
```

### 前端核心依赖 (package.json)

```json
{
  "dependencies": {
    // === 核心框架 ===
    "next": "^16.1.7",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    
    // === AI 集成 ===
    "ai": "^6.0.33",
    "@langchain/langgraph-sdk": "^1.5.3",
    
    // === UI 组件 ===
    "tailwindcss": "^4.0.15",
    "sonner": "^2.0.7",
    "@radix-ui/react-*": "多组件",
    
    // === 专业组件 ===
    "@xyflow/react": "^12.10.0",      // 流程图
    "@uiw/react-codemirror": "^4.25.4", // 代码编辑
    
    // === 工具库 ===
    "zod": "^3.24.2",
    "gsap": "^3.13.0",
    "motion": "^12.26.2"
  }
}
```

### 依赖复杂度评估

| 评估维度 | 评分 | 说明 |
|----------|------|------|
| **直接依赖数量** | ⭐⭐⭐ (中等) | 约 15-20 个主要后端依赖 |
| **间接依赖数量** | ⭐⭐⭐⭐ (较高) | 考虑 FastAPI + LangChain 生态链 |
| **依赖来源多样性** | ⭐⭐⭐⭐ (高) | 涵盖 AI、IM、通信等多领域 |
| **版本约束宽松度** | ⭐⭐⭐⭐⭐ (优秀) | 大多使用 >= 约束 |
| **过时风险** | ⭐⭐⭐ (中等) | 需关注 LangChain 版本更新 |

### 依赖健康度分析

```
后端依赖层级结构:
├── fastapi (核心)
│   ├── pydantic (数据验证)
│   ├── starlette (ASGI)
│   └── uvicorn (服务器)
│
├── langgraph-sdk (AI 编排)
│   ├── langchain-core
│   ├── langchain-community
│   └── httpx
│
└── IM SDKs (独立)
    ├── lark-oapi
    ├── slack-sdk
    └── python-telegram-bot
```

**优点**：

- 依赖版本约束宽松，避免锁死导致的兼容性问题
- 使用 uv 作为包管理器，依赖解析和安装速度快
- Workspace 结构支持 harness 包独立发布

**风险**：

- LangChain 生态系统更新频繁，需关注 breaking changes
- 多个 IM SDK 依赖，API 变更需同步更新
- Next.js 16.1.7 版本号较大，需确认版本真实性

---

## 可运行性评估

### 构建工具链 (Makefile)

```makefile
# 配置管理
make config              # 生成配置文件

# 开发环境
make dev                 # 启动本地开发
make check               # 前置环境检查

# Docker 环境
make docker-init         # 初始化 Docker (拉取镜像)
make docker-start        # 启动 Docker 开发环境
make docker-stop         # 停止 Docker 环境

# 生产环境
make up                  # 生产环境部署
make down                 # 停止生产环境

# 工具
make install             # 安装依赖
```

### 前置环境要求

| 工具 | 版本要求 | 用途 |
|------|----------|------|
| **Node.js** | ≥ 22 | 前端运行时 |
| **pnpm** | ≥ 10.26.2 | 前端包管理 |
| **uv** | 最新 | Python 包管理 |
| **nginx** | 最新 | 反向代理 |
| **Docker** | 最新 | 沙箱隔离 |

### 启动模式分析

| 模式 | 进程数 | 组成 | 适用场景 |
|------|--------|------|----------|
| **标准 Dev** | 4 | frontend + gateway + langgraph + nginx | 完整开发调试 |
| **标准 Prod** | 4 | 同上，预构建镜像 | 生产部署 |
| **Gateway Dev** | 3 | frontend + gateway (嵌入运行时) + nginx | 轻量开发 |
| **Gateway Prod** | 3 | 同上，生产级别 | 简化部署 |

### Docker 部署架构

```
docker-compose 服务组成:
├── frontend      # Next.js 应用 (Port 2026)
├── gateway       # FastAPI 网关 (Port 8001)
├── langgraph     # LangGraph 服务器 (Port 2024)
├── nginx         # 反向代理 + WebSocket
└── sandbox       # 隔离执行环境
```

### 沙箱执行模式

| 模式 | 隔离级别 | 适用场景 | 配置方式 |
|------|----------|----------|----------|
| **Local** | 无隔离 | 开发调试 | `use: deerflow.community.local_sandbox` |
| **Docker** | 容器级 | 单机部署 | `use: deerflow.community.docker_sandbox` |
| **Kubernetes** | Pod 级 | 生产大规模 | `use: deerflow.community.aio_sandbox` |

### 可运行性评分

| 评估维度 | 评分 | 说明 |
|----------|------|------|
| **文档完整性** | ⭐⭐⭐⭐⭐ | README 36KB+，多语言文档 |
| **配置自动化** | ⭐⭐⭐⭐⭐ | `make config` 自动生成 |
| **Docker 支持** | ⭐⭐⭐⭐⭐ | 一键启动，开箱即用 |
| **本地开发体验** | ⭐⭐⭐⭐ | `make dev` 简化流程 |
| **环境隔离** | ⭐⭐⭐⭐⭐ | Sandbox 多模式支持 |

### 快速启动指南

**方式一：Docker (推荐)**

```bash
# 1. 克隆
git clone https://github.com/bytedance/deer-flow.git
cd deer-flow

# 2. 生成配置
make config

# 3. 配置 API Keys
# 编辑 config.yaml 和 .env

# 4. 启动开发环境
make docker-init  # 首次运行
make docker-start # 启动服务

# 5. 访问
open http://localhost:2026
```

**方式二：本地开发**

```bash
# 1. 前置检查
make check  # Node.js 22+, pnpm, uv, nginx

# 2. 安装依赖
make install

# 3. 启动服务
make dev

# 4. 访问
open http://localhost:2026
```

---

## 技术亮点

### 架构设计亮点

#### 亮点 1: 前后端分离 + API 网关模式

```
优势:
├── 前端独立部署，不依赖后端渲染
├── Gateway 作为统一入口，聚合多个服务
├── 支持 IM 渠道接入，无需前端参与
└── 便于微服务拆分和扩展
```

#### 亮点 2: Workspace Monorepo 结构

```toml
# pyproject.toml
[tool.uv.workspace]
members = ["packages/harness"]
```

```
好处:
├── harness 可作为独立 PyPI 包发布
├── 清晰的包边界
├── 便于版本管理和发布
└── 支持 monorepo 依赖管理
```

#### 亮点 3: 多沙箱执行模式

| 模式 | 隔离级别 | 适用场景 |
|------|----------|----------|
| **Local** | 无隔离 | 开发调试 |
| **Docker** | 容器级 | 单机部署 |
| **Kubernetes** | Pod 级 | 生产大规模 |

#### 亮点 4: 技能系统设计

```
技能定义 (SKILL.md):
├── Markdown 格式，易于编写和维护
├── 包含工作流、最佳实践、参考资源
├── 支持版本控制和分享
└── 内置 7 个技能 + 自定义扩展
```

### 技术选型亮点

| 领域 | 技术选型 | 亮点分析 |
|------|----------|----------|
| **Python 包管理** | uv | 比 pip/poetry 更快，支持 workspace |
| **前端状态** | TanStack Query | 专为服务端状态设计，缓存强大 |
| **流程可视化** | @xyflow/react | 专为 AI Agent 流程设计 |
| **代码展示** | CodeMirror 6 | 可扩展，支持语法高亮 |
| **动画** | GSAP + motion | 工业级动画方案 |
| **IM 集成** | 多渠道 SDK | 支持飞书/Slack/Telegram/企业微信 |

### 开发者体验亮点

```
1. 一键配置: make config
2. 一键开发: make dev
3. 一键部署: make docker-start
4. 详细文档: 多语言 README + 详细 CONFIGURATION.md
5. 贡献友好: 完整的 CONTRIBUTING.md
```

### 推荐模型

- **Doubao-Seed-2.0-Code** (豆包)
- **DeepSeek v3.2**
- **Kimi 2.5** (月之暗面)
- **OpenAI GPT-4**
- **Claude Sonnet 4.6**
- 支持 OpenAI、OpenRouter、vLLM、Claude Code、Codex 等

---

## 潜在问题

### 安全风险

#### 🔴 高风险: 本地部署安全

```
问题描述:
├── 默认监听 127.0.0.1，依赖本地网络信任
├── 包含系统命令执行能力
├── 无内置认证机制
└── 文件系统读写权限

建议:
├── 生产环境必须配合认证网关
├── IP 白名单控制
├── 网络隔离
└── 定期更新依赖
```

> ⚠️ **重要**：DeerFlow 默认部署在本地可信环境 (127.0.0.1)，包含高权限操作如系统命令执行。

#### 🟡 中风险: 外部 API 依赖

| API | 风险类型 | 影响 |
|-----|----------|------|
| OpenAI | 密钥泄露、成本超支 | 数据安全、财务 |
| Tavily | 服务可用性 | 功能受限 |
| LangSmith/Langfuse | 数据隐私 | 追踪数据外传 |

### 技术债务风险

#### 🟡 依赖管理风险

```
风险点:
├── LangChain 生态系统更新频繁
│   └── 可能出现 breaking changes
├── 多个 IM SDK 依赖
│   └── API 变更需同步更新
├── Next.js 16.1.7 版本号
│   └── 疑似未来版本 (2026)
└── Python 3.12+ 要求
    └── 某些环境受限
```

#### 🟡 架构复杂度

```
复杂度来源:
├── 多进程部署 (4 个服务)
├── 多种运行模式
├── 多渠道集成
└── 沙箱执行环境

管理难点:
├── 故障排查涉及多个服务
├── 资源占用较高
└── 配置项众多
```

### 可维护性风险

| 风险点 | 说明 | 缓解措施 |
|--------|------|----------|
| **多语言代码库** | Python + TypeScript | 文档清晰 |
| **大量外部集成** | IM 渠道 SDK | 抽象接口层 |
| **配置复杂性** | 29KB 配置模板 | 配置文档详细 |
| **社区活跃度** | 500+ open issues | 持续维护中 |

---

## 总结与建议

### 项目定位

DeerFlow 是一个**功能完整的 AI 智能体运行平台**，技术上处于领先水平，适合以下场景：

- ✅ 深度研究和报告生成
- ✅ 代码编写和调试
- ✅ 多步骤复杂任务自动化
- ✅ 构建 AI 助手应用
- ✅ 企业内部自动化工作流

### 技术优势

| 优势 | 说明 |
|------|------|
| **现代化技术栈** | Python 3.12+ / Next.js 16 / React 19 |
| **成熟的 AI 框架** | 基于 LangGraph + LangChain |
| **优秀的开发者体验** | Makefile 自动化、Docker 一键部署 |
| **高度可扩展** | 技能系统、Python SDK、多渠道集成 |
| **活跃的社区** | 58K Stars，持续维护 |

### 综合评分

| 评估维度 | 评分 | 权重 | 加权得分 |
|----------|------|------|----------|
| **技术栈现代性** | ⭐⭐⭐⭐⭐ | 15% | 0.75 |
| **架构设计** | ⭐⭐⭐⭐⭐ | 20% | 1.00 |
| **依赖管理** | ⭐⭐⭐⭐ | 15% | 0.60 |
| **可运行性** | ⭐⭐⭐⭐⭐ | 20% | 1.00 |
| **代码质量** | ⭐⭐⭐⭐ | 15% | 0.60 |
| **文档完善度** | ⭐⭐⭐⭐⭐ | 10% | 0.50 |
| **安全考量** | ⭐⭐⭐ | 5% | 0.15 |
| **综合评分** | **⭐⭐⭐⭐⭐ (4.6/5)** | 100% | **4.60** |

### 使用建议

| 场景 | 建议 |
|------|------|
| **个人开发者** | 使用 Docker 部署，开箱即用 |
| **企业用户** | 配合认证网关，做好网络隔离 |
| **二次开发** | 利用 Python SDK，基于 harness 包构建 |
| **学习研究** | 代码结构清晰，适合学习 Agent 架构 |

### 改进建议

| 优先级 | 建议 | 说明 |
|--------|------|------|
| **高** | 安全增强 | 增加内置认证机制 |
| **中** | 依赖管理 | 考虑使用 pip-tools 锁定依赖版本 |
| **中** | 监控告警 | 增加内置指标暴露 |
| **低** | 文档优化 | 增加架构图和流程图 |

---

## 附录: 配置文件详解

### 模型配置示例 (config.yaml)

```yaml
models:
  - name: gpt-4
    display_name: GPT-4
    use: langchain_openai:ChatOpenAI
    model: gpt-4
    api_key: $OPENAI_API_KEY
    max_tokens: 4096
    temperature: 0.7

  - name: claude-sonnet-4.6
    display_name: Claude Sonnet 4.6
    use: deerflow.models.claude_provider:ClaudeChatModel
    model: claude-sonnet-4-6
    supports_thinking: true

  - name: qwen3-32b-vllm
    display_name: Qwen3 32B (vLLM)
    use: deerflow.models.vllm_provider:VllmChatModel
    base_url: http://localhost:8000/v1
    supports_thinking: true
```

### 沙箱配置

```yaml
sandbox:
  # 本地模式
  use: deerflow.community.local_sandbox:LocalSandboxProvider
  
  # Docker 模式
  # use: deerflow.community.docker_sandbox:DockerSandboxProvider
  # docker_image: deerflow/sandbox:latest
  
  # Kubernetes 模式
  # use: deerflow.community.aio_sandbox:AioSandboxProvider
  # provisioner_url: http://localhost:8080
```

### IM 渠道配置

```yaml
channels:
  langgraph_url: http://localhost:2024
  gateway_url: http://localhost:8001
  
  telegram:
    enabled: true
    bot_token: $TELEGRAM_BOT_TOKEN
    
  slack:
    enabled: true
    bot_token: $SLACK_BOT_TOKEN
    app_token: $SLACK_APP_TOKEN
    
  feishu:
    enabled: true
    app_id: $FEISHU_APP_ID
    app_secret: $FEISHU_APP_SECRET
```

### 环境变量模板 (.env.example)

```bash
# API Keys
OPENAI_API_KEY=your-openai-api-key
TAVILY_API_KEY=your-tavily-api-key
INFOQUEST_API_KEY=your-infoquest-api-key

# IM Channels
TELEGRAM_BOT_TOKEN=xxx
SLACK_BOT_TOKEN=xoxb-xxx
SLACK_APP_TOKEN=xapp-xxx
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
WECOM_BOT_ID=xxx
WECOM_BOT_SECRET=xxx

# Tracing
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_xxx
LANGFUSE_TRACING=true
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
```