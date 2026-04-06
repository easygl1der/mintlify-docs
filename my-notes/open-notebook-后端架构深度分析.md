---
title: Open Notebook 后端架构深度分析
description: Python FastAPI + SurrealDB + LangGraph 全栈技术架构详解
---

# Open Notebook 后端架构深度分析

import { Callout } from 'nextra/components'

<Callout type="info">
完整报告源文件: `/Volumes/SSK SSD/Projects/open-notebook-backend-analysis.md`
</Callout>

## 1. 项目核心原理

### 1.1 项目定位

**Open Notebook** 是一个开源的、隐私优先的 Google NotebookLM 替代方案：

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

---

## 2. 后端架构详解

### 2.1 FastAPI 应用结构

**入口**: `api/main.py` — 标准的 FastAPI lifespan 应用

关键组件：
- `PasswordAuthMiddleware` — 简单密码认证中间件（排除 `/health`, `/docs`, `/api/auth/status`, `/api/config`）
- `CORS middleware` — 允许所有 origin（生产环境需配置）
- 19 个 Router 模块注册在主应用
- `AsyncMigrationManager` — 启动时自动执行数据库迁移

**Router 层** — 21 个端点模块：
`auth, chat, commands, config, context, credentials, embedding, embedding_rebuild, episode_profiles, insights, languages, models, notebooks, notes, podcasts, search, settings, source_chat, sources, speaker_profiles, transformations`

### 2.2 LangGraph 工作流

`open_notebook/graphs/` 中的 5 种 workflow：
- `source.py` — 内容摄取工作流（提取 → embedding → 保存）
- `chat.py` — 对话 agent，含 message history
- `ask.py` — 搜索 + 综合（检索相关 source → LLM 生成答案）
- `source_chat.py` — 基于 source 的上下文聊天
- `transformation.py` — 源内容自定义转换

使用 `langgraph-checkpoint-sqlite` 做状态持久化。

### 2.3 AI 层 (`open_notebook/ai/`)

- `ModelManager` — 模型工厂，支持从 DB 读取 credential 或 env var fallback
- `Esperanto` 库: 统一创建 language/embedding/speech_to_text/text_to_speech 模型
- `provision.py` — 根据 content 大小自动选择模型（>105k tokens 用 large_context_model）

---

## 3. 数据库设计

### 3.1 SurrealDB 使用方式

SurrealDB 运行在 rocksdb 持久化模式，WebSocket RPC 连接。

**为什么选 SurrealDB**:
1. 内置向量存储 + 向量相似度搜索
2. 图关系模型
3. 内嵌全文搜索（BM25）
4. Schemafull/Schemaless 灵活模式

### 3.2 核心表结构

| 表名 | 类型 | 说明 |
|------|------|------|
| `notebook` | SCHEMAFULL | 笔记本主记录 |
| `source` | SCHEMAFULL | 源内容（PDF/URL/文本） |
| `source_embedding` | SCHEMAFULL | source 的分块 embedding |
| `source_insight` | SCHEMAFULL | AI 生成的洞察 |
| `note` | SCHEMAFULL | 用户/AI 笔记，含 embedding |
| `reference` | RELATION | source → notebook 多对多关系 |

---

## 4. Claude Code Harness 接入可行性

| 场景 | 可行性 | 结论 |
|------|--------|------|
| MCP 协议直接对接（已有 open-notebook-mcp，39 tools） | 85% 高 | 零开发可用 |
| 深度 Agentic 集成 | 40-55% 中低 | 需 3-4 周 LangGraph Wrapper 改造 |

---

## 5. 技术风险

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| SurrealDB v2 成熟度 | 中 | 关注 embedded 模式 |
| CORS 全开 | 高 | 生产需配置 allow_origins |
| 认证简单 | 高 | dev-only，生产需 OAuth/JWT |
| Esperanto 版本约束 &lt;3 | 中 | 升级路径需规划 |
