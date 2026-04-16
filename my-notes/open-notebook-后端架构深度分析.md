---
title: Open Notebook 后端架构深度分析
description: Python FastAPI + SurrealDB + LangGraph 全栈技术架构详解
---

# Open Notebook 后端架构深度分析报告

## 1. 项目核心原理

### 1.1 项目定位

**Open Notebook** 是一个开源的、隐私优先的 Google Notebook LM 替代方案。项目核心理念：

- **数据主权**: 所有内容完全自托管，不依赖任何云服务
- **多模型支持**: 支持 16+ AI provider（OpenAI、Anthropic、Ollama、LM Studio、Google、Groq、Mistral、DeepSeek 等）
- **多模态内容**: PDF、视频、音频、网页、Office 文档统一管理
- **生成式能力**: AI 播客生成（1-4 发言者）、智能笔记、语义搜索、上下文感知聊天

### 1.2 核心架构哲学

```
三层分离 + 图数据库 + LangGraph 工作流
```

- **Frontend** (Next.js/React) - 用户交互层，端口 3000
- **API** (FastAPI) - 业务逻辑编排层，端口 5055
- **Database** (SurrealDB) - 图存储层，端口 8000

关键设计决策：
- **全异步**: 所有 DB 查询、LLM 调用、API 请求均为 async/await
- **LangGraph 状态机**: 复杂工作流（内容摄取、聊天、搜索综合）使用状态机管理
- **Esperanto 库**: 统一的 8+ AI provider 接口，消除 provider lock-in
- **SurrealDB 图模型**: 同时支持关系型查询 + 向量搜索，无需独立向量数据库

---

## 2. 后端架构详解

### 2.1 FastAPI 应用结构 (`api/`)

**入口**: `api/main.py` — 标准的 FastAPI lifespan 应用

关键组件：
- `PasswordAuthMiddleware` — 简单密码认证中间件（排除 `/health`, `/docs`, `/api/auth/status`, `/api/config`）
- `CORS middleware` — 允许所有 origin（生产环境需配置）
- 19 个 Router 模块注册在主应用
- `AsyncMigrationManager` — 启动时自动执行数据库迁移

**Router 层** (`api/routers/`) — 21 个端点模块：
```
auth, chat, commands, config, context, credentials,
embedding, embedding_rebuild, episode_profiles,
insights, languages, models, notebooks, notes,
podcasts, search, settings, source_chat, sources,
speaker_profiles, transformations
```

**Service 层** (`api/*_service.py`) — 业务逻辑封装：
- `ChatService`, `NotebookService`, `SourcesService`, `ModelsService`
- `CredentialsService`, `PodcastApiService`, `EmbeddingService`
- 使用 `httpx.AsyncClient` 调用自身 API，支持长超时（10min for read）

**Client 层** (`api/client.py`) — 完整的 REST API 客户端：
- 提供所有 API 的同步/异步封装
- 超时默认 300s，支持环境变量 `API_CLIENT_TIMEOUT` 配置
- Bearer token 认证支持

### 2.2 核心库结构 (`open_notebook/`)

```
open_notebook/
  ai/           - AI 模型管理与 provisioning
  database/     - SurrealDB 连接与仓储模式
  domain/       - 领域模型（Notebook, Source, Note, Credential）
  graphs/       - LangGraph 工作流定义
  podcasts/      - 播客生成逻辑
  utils/        - 加密、token 计算等工具
```

**AI 层** (`open_notebook/ai/`):
- `ModelManager` — 模型工厂，支持从 DB 读取 credential 或 env var fallback
- `model_discovery.py` — 动态发现 provider 支持的模型列表
- `connection_tester.py` — 测试各 provider 连接性
- `provision.py` — 根据 content 大小自动选择模型（>105k tokens 用 large_context_model）
- `Esperanto` 库: 统一创建 language/embedding/speech_to_text/text_to_speech 模型

**LangGraph 工作流** (`open_notebook/graphs/`):
- `source.py` — 内容摄取工作流（提取 → embedding → 保存）
- `chat.py` — 对话 agent，含 message history
- `ask.py` — 搜索 + 综合（检索相关 source → LLM 生成答案）
- `source_chat.py` — 基于 source 的上下文聊天
- `transformation.py` — 源内容自定义转换
- 使用 `langgraph-checkpoint-sqlite` 做状态持久化（SQLite checkpointer）

**Domain 层** (`open_notebook/domain/`):
- `base.py` — ObjectModel（带 created/updated 时间戳）、RecordModel（单例记录如 default_models）
- `notebook.py` — Notebook 模型，含 source/note 关系管理
- `credential.py` — 加密存储的 API key
- `provider_config.py` — Provider 配置管理
- `content_settings.py` — 分块策略配置

### 2.3 命令行工具 (`commands/`)

```
commands/
  embedding_commands.py  - 嵌入生成命令（27KB，rebuild 逻辑）
  source_commands.py    - 源内容处理命令
  podcast_commands.py    - 播客生成命令（11KB）
  example_commands.py    - 示例命令
```

使用 `surreal-commands` 库做异步任务队列，通过 `AsyncMigrationManager` 在 API 启动时导入注册。

### 2.4 依赖管理 (`pyproject.toml`)

关键依赖（Python 3.11+）:
- `fastapi>=0.104.0`, `uvicorn>=0.24.0`
- `langchain>=1.2.0`, `langgraph>=1.0.5`
- `surrealdb>=1.0.4` — 异步 DB driver
- `esperanto>=2.19.7`, `<3` — 自研的统一 AI provider 库（lfnovo）
- `content-core>=1.14.1`, `<2` — 内容提取（PDF/URL/音视频）
- `podcast-creator>=0.12.0`, `<1` — 播客生成
- `surreal-commands>=1.3.1`, `<2` — 异步任务队列
- `tiktoken>=0.12.0` — OpenAI tokenizer（用于 token 计数和 context 管理）

---

## 3. 数据库设计

### 3.1 SurrealDB 使用方式

SurrealDB 运行在 rocksdb 持久化模式，WebSocket RPC 连接：
```
SURREAL_URL=ws://surrealdb:8000/rpc
SURREAL_NAMESPACE=open_notebook
SURREAL_DATABASE=open_notebook
```

**为什么选 SurrealDB**:
1. 内置向量存储 + 向量相似度搜索（`vector::similarity::cosine`）
2. 图关系模型（`TYPE RELATION FROM source TO notebook`）
3. 内嵌全文搜索（`SEARCH ANALYZER ... BM25 HIGHLIGHTS`）
4. Schemafull/Schemaless 灵活模式
5. 单一数据库同时满足结构化数据 + 非结构化搜索

### 3.2 数据模型

**核心表** (Migration 1 定义):
| 表名 | 类型 | 说明 |
|------|------|------|
| `notebook` | SCHEMAFULL | 笔记本主记录 |
| `source` | SCHEMAFULL | 源内容（PDF/URL/文本），含 title/topics/full_text/asset |
| `source_embedding` | SCHEMAFULL | source 的分块 embedding（source, order, content, embedding） |
| `source_insight` | SCHEMAFULL | AI 生成的洞察（source, insight_type, content, embedding） |
| `note` | SCHEMAFULL | 用户/AI 笔记，含 embedding |
| `reference` | RELATION | source → notebook 多对多关系 |
| `artifact` | RELATION | note → notebook 多对多关系 |
| `podcast_config` | SCHEMALESS | 播客配置 |
| `model` | - | AI 模型注册（name, provider, type, credential） |
| `open_notebook:default_models` | RECORD | 单例默认模型配置 |

**搜索函数** (Migration 1 定义 SurrealQL 函数):
- `fn::text_search()` — BM25 全文搜索，跨 source/notes 多个字段
- `fn::vector_search()` — 余弦相似度向量搜索，返回最相关结果

### 3.3 迁移机制

**AsyncMigrationManager** (`open_notebook/database/async_migrate.py`):
- 迁移文件命名: `N.surrealql` (N = 序号), `N_down.surrealql` (回滚)
- 当前版本: 14 个迁移 (1.surrealql ~ 14.surrealql)
- 启动时自动检测: 比较迁移文件名序号与 DB 中记录的 version
- **Fail-Fast 策略**: 迁移失败则 API 不启动，保证 schema 一致性
- 迁移内容示例:
  - Migration 3: `chat_session`, `chat_message` 表 + 关系定义
  - Migration 5: `transformation` 表 + 内置 transformation 记录
  - Migration 7: `episode_profile`, `speaker_profile` 表
  - Migration 9: `api_key` 表（认证）

---

## 4. 部署方案

### 4.1 Docker / Docker Compose 配置

**双服务架构** (`docker-compose.yml`):
```yaml
services:
  surrealdb:
    image: surrealdb/surrealdb:v2
    command: start --log info --user root --pass root rocksdb:/mydata/mydatabase.db
    ports: ["8000:8000"]
    volumes: ./surreal_data:/mydata

  open_notebook:
    image: lfnovo/open_notebook:v1-latest
    ports: ["8502:8502", "5055:5055"]
    environment:
      - OPEN_NOTEBOOK_ENCRYPTION_KEY=change-me-to-a-secret-string
      - SURREAL_URL=ws://surrealdb:8000/rpc
    volumes: ./notebook_data:/app/data
```

### 4.2 Dockerfile 多阶段构建

**Builder stage**: `python:3.12-slim-bookworm` + Node.js 20
- `uv sync --frozen` 安装 Python 依赖
- 预下载 `tiktoken` encoding（离线可用）
- `npm ci + npm run build` 构建 Next.js 前端

**Runtime stage**: 相同基础镜像
- 只复制 `.venv` (预装 Python 包) + 源码 + 前端 build 产物
- supervisord 管理进程（Next.js + API）
- 暴露 8502 (frontend) + 5055 (API)

### 4.3 Makefile 命令解析

| 命令 | 说明 |
|------|------|
| `make database` | 仅启动 SurrealDB |
| `make api` | `uv run run_api.py` 启动 API（开发模式） |
| `make worker-start` | `surreal-commands-worker` 启动异步任务 worker |
| `make start-all` | 依次启动: DB(3s) → API(&) → Worker(&) → Frontend |
| `make docker-push` | 多平台构建 (linux/amd64,linux/arm64) → Docker Hub + GHCR |
| `make docker-release` | push 版本 tag + 更新 v1-latest |
| `make lint` | `uv run mypy .` 类型检查 |

### 4.4 环境变量配置

**.env.example 关键变量**:
```bash
OPEN_NOTEBOOK_ENCRYPTION_KEY=     # 必填，API key 加密密钥
SURREAL_URL=ws://surrealdb:8000/rpc
SURREAL_USER=root
SURREAL_PASSWORD=root
SURREAL_NAMESPACE=open_notebook
SURREAL_DATABASE=open_notebook
OPEN_NOTEBOOK_PASSWORD=           # 可选，API Bearer 认证
API_CLIENT_TIMEOUT=300.0          # API 客户端超时(s)
CHUNK_SIZE=1500                   # 内容分块大小
CHUNK_OVERLAP=150                 # 分块重叠
OLLAMA_BASE_URL=http://ollama:11434
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=secret
```

### 4.5 生产级部署要点

1. **必改项**: `OPEN_NOTEBOOK_ENCRYPTION_KEY` 必须替换为强随机密钥
2. **CORS**: 当前允许所有 origin，需配置 `allow_origins` 为特定域名
3. **反向代理**: 文档有 nginx/caddy/traefik 配置示例
4. **数据持久化**: `./surreal_data` 和 `./notebook_data` 目录必须持久化
5. **监控**: 日志输出到 stdout/stderr（supervisord 收集）
6. **迁移**: 首次启动自动执行，后续升级时 API 重启自动运行
7. **多平台构建**: `PLATFORMS=linux/amd64,linux/arm64` 支持 Apple Silicon

---

## 5. Claude Code Harness 接入可行性分析

### 5.1 概念澄清

**Claude Code Harness** 存在两种理解：

**理解 A（官方 CLI Harness）**: Anthropic 的 Claude Code 终端工具本身就是一个 AI Coding Agent，通过 MCP (Model Context Protocol) 与外部工具通信。这是狭义的 "harness"。

**理解 B（Agentic Harness 框架）**: 任何用于驱动 AI Agent 与外部系统交互的协议框架，包括 MCP、function calling、tool use 等。这是广义的理解。

### 5.2 MCP 现状分析

Open Notebook **已有 MCP 服务**：

**官方 MCP Server**: [Epochal-dev/open-notebook-mcp](https://github.com/Epochal-dev/open-notebook-mcp)
- 已发布到 PyPI (`open-notebook-mcp`)
- 暴露 **39 个 tools**，覆盖:
  - Notebooks (5): list, get, create, update, delete
  - Sources (5): 管理链接/文件/文本源
  - Notes (5): 创建和组织笔记
  - Search (3): 向量/文本搜索
  - Models (5): AI 模型配置
  - Chat (7): 会话管理
  - Settings (2): 应用设置
- 支持 STDIO 和 Streamable HTTP 两种传输层
- 连接方式：
  ```json
  {
    "mcpServers": {
      "open-notebook": {
        "command": "uvx",
        "args": ["open-notebook-mcp"],
        "env": {
          "OPEN_NOTEBOOK_URL": "http://localhost:5055",
          "OPEN_NOTEBOOK_PASSWORD": "your_password"
        }
      }
    }
  }
  ```

### 5.3 直接 Harness 协议对接的可行性

**如果 "Harness" = MCP 协议**:

**可行性评估: 高 (85%)**

| 维度 | 评分 | 说明 |
|------|------|------|
| 协议匹配 | ✅ 完全匹配 | MCP 是开放标准，open-notebook-mcp 已完整实现 |
| 工具丰富度 | ✅ 39 tools | 覆盖所有核心 CRUD + 搜索 + AI 交互 |
| 传输层 | ✅ STDIO/HTTP | 完美支持 Claude Code 的 MCP 传输 |
| 认证 | ✅ Bearer token | 已支持 API 密码认证 |
| 部署难度 | ✅ 零开发 | 现有 MCP server 可直接使用 |

**但存在优化空间**:
1. MCP server 是独立项目，不在主仓库维护
2. 工具粒度偏粗（list/get/create/update/delete），缺乏细粒度操作
3. 不支持流式响应（streaming）

---

### 5.4 如果" Harness" = 深度 Agentic 集成

**可行性评估: 中低 (40-55%)**

如果目标是将 Claude Code 直接作为 Open Notebook 的前端 Agent（用户通过自然语言操作 Notebook），则需要架构改造。

**当前架构障碍**:

1. **缺乏 Agent 协议层**: FastAPI 是 REST API，不是 Agent Protocol。Claude Code 使用的是类似 MCPO (MCP over HTTP) 或自定义 agentic 协议，不能简单对接。

2. **状态管理不兼容**: Claude Code 是会话级的 CLI 工具，Open Notebook 是无状态的 REST API。Agent 需要:
   - 维护多轮对话状态
   - 追踪 Agent 在 Notebook 中的"当前位置"
   - 处理长时间运行的操作（podcast 生成可能需要几分钟）

3. **安全边界**: Open Notebook 的 MCP server 需要 API key 认证，Claude Code 需要安全地传递凭证

4. **工具粒度**: 现有 API 是粗粒度的 CRUD，Agent 需要细粒度操作（如"将这个 PDF 的第 3 页添加到笔记本的'机器学习'分类下"）

**实现路径建议**:

如果目标是深度集成（让 Claude Code Agent 直接操作 Open Notebook），建议以下架构改造：

```
方案 A: MCP Server 增强 (推荐, 2-3 周)
├── 在现有 open-notebook-mcp 基础上
├── 添加 streaming 支持 (Server-Sent Events)
├── 添加细粒度工具 (chunk-level 操作, embedding 控制)
└── 状态管理扩展 (支持多轮 Agent 对话)

方案 B: 直接 Agent Protocol (4-6 周)
├── 实现 Anthropic 的 Agent Protocol 草案
│   (参考 Claude Code 内部使用的协议)
├── 添加 WebSocket 支持
├── 实现 Agent 状态机
└── 重构部分 API 为 tool-call 模式

方案 C: LangGraph Agent Wrapper (3-4 周)
├── 用 LangGraph 封装 Open Notebook API
├── 暴露为可被调用的 Tool
├── 支持多步复杂操作（research workflow）
└── 通过 MCP 暴露给 Claude Code
```

### 5.5 架构改造建议（深度集成场景）

如果要实现 Claude Code Agent 对 Open Notebook 的深度控制，推荐：

```python
# 新增文件: open_notebook/agent/protocol.py
# 实现 Agent Protocol (类似 MCPO)

from fastapi import APIRouter, WebSocket
from typing import AsyncIterator

router = APIRouter()

@router.websocket("/agent")
async def agent_endpoint(websocket: WebSocket):
    """Claude Code Agent WebSocket 端点"""
    await websocket.accept()
    try:
        async for message in websocket.iter_text():
            # 解析 agent 协议消息
            # 调用 LangGraph workflow
            # 流式返回结果
            ...
    finally:
        await websocket.close()
```

关键实现要点：
1. **WebSocket 传输**: Claude Code 支持 WebSocket 的 Agent 通信
2. **Streaming Response**: 实现 SSE/流式 JSON 响应
3. **Tool Registry**: 将现有 API 工具注册为 Agent Tools
4. **Session 管理**: 支持多轮对话状态

---

## 6. 技术风险与机遇

### 6.1 技术风险

| 风险 | 等级 | 描述 | 缓解措施 |
|------|------|------|----------|
| SurrealDB v2 成熟度 | 中 | v2 版本相对较新，rocksdb 存储引擎在某些场景有性能问题 | 关注官方 release note，有嵌入式 (embedded) 模式可考虑 |
| 迁移机制脆弱性 | 中 | fail-fast 策略好，但迁移文件顺序管理依赖文件名约定 | 添加迁移验证测试 |
| 多 worker 并发写入 | 中 | SQLite checkpointer + SurrealDB 并发可能有事务冲突 | 日志中 transaction conflict 已有 debug 处理 |
| CORS 全开 | 高 | 生产环境 allow_origins=["*"] 有安全风险 | 文档已提及需配置 |
| 认证简单 | 高 | PasswordAuthMiddleware 仅用于开发 | 文档建议生产用 OAuth/JWT |
| MCP Server 独立维护 | 低 | open-notebook-mcp 在独立仓库，与主版本可能同步不及时 | 考虑合并到主仓库 |

### 6.2 技术机遇

| 机遇 | 描述 |
|------|------|
| **多模型路由优化** | `provision_langchain_model()` 已实现按 content size 自动路由，可扩展为按 cost/latency 路由 |
| **RAG 增强** | 已有 `fn::vector_search` 和 `fn::text_search`，可扩展为混合搜索 (hybrid search) |
| **实时协作** | SurrealDB 支持实时订阅 (live query)，可实现多用户实时协作 |
| **Agentic 搜索** | LangGraph ask workflow 可扩展为多跳推理 (multi-hop reasoning) |
| **跨笔记本源共享** | Roadmap 中提到，意义重大（一个 source 供多个 notebook 使用）|
| **本地模型优化** | Ollama 集成已完善，可进一步优化 quantized model 使用 |

---

## 附录 A: API 端点总览

| Router | 前缀 | 主要端点 |
|--------|------|----------|
| notebooks | /api/notebooks | GET(list), POST(create), GET/{id}, PUT/{id}, DELETE/{id} |
| sources | /api/sources | 同上 + /{id}/status, /{id}/insights |
| notes | /api/notes | CRUD + /{id}/save |
| chat | /api/chat | /sessions, /sessions/{id}, /execute, /context |
| search | /api/search | POST(混合搜索), /ask/* |
| embeddings | /api/embeddings | /rebuild, /{id}/status |
| models | /api/models | CRUD + /defaults |
| credentials | /api/credentials | CRUD + /test |
| podcasts | /api/podcasts | CRUD + /execute |
| transformations | /api/transformations | CRUD + /execute |
| commands | /api/commands | /{id}/status |

---

## 附录 B: 数据库 Schema 摘要 (Migration 1)

```sql
-- 核心表
DEFINE TABLE notebook SCHEMAFULL;
DEFINE TABLE source SCHEMAFULL;        -- 含 asset(JSON), title, topics, full_text
DEFINE TABLE source_embedding SCHEMAFULL;  -- 分块内容 + embedding 向量
DEFINE TABLE source_insight SCHEMAFULL;    -- AI 洞察
DEFINE TABLE note SCHEMAFULL;          -- 含 embedding

-- 关系表
DEFINE TABLE reference TYPE RELATION FROM source TO notebook;
DEFINE TABLE artifact TYPE RELATION FROM note TO notebook;

-- 搜索索引
DEFINE INDEX idx_source_title ON source COLUMNS title SEARCH ANALYZER my_analyzer BM25;
DEFINE INDEX idx_source_full_text ON source COLUMNS full_text SEARCH ANALYZER my_analyzer BM25;
DEFINE INDEX idx_source_embed_chunk ON source_embedding COLUMNS content SEARCH ANALYZER my_analyzer BM25;
DEFINE INDEX idx_note ON note COLUMNS content SEARCH ANALYZER my_analyzer BM25;

-- 搜索函数
DEFINE FUNCTION fn::text_search(...);   -- 跨表 BM25 搜索
DEFINE FUNCTION fn::vector_search(...); -- 余弦相似度向量搜索
```

---

*报告生成时间: 2026-04-06*
*分析基于 commit: c42dc10d2baa8de443122bc200cddc3f695bdbe8*
