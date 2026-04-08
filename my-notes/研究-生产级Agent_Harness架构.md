---
title: 生产级 Agent Harness 框架调研：LangGraph + FastAPI + Langfuse + pgvector + MCP
description: 完整架构图、FastAPI 层设计、Langfuse 可观测性、PostgreSQL/pgvector 存储方案、MCP 工具协议、前端 Next.js + Zustand
---

# 生产级 Agent Harness 框架调研：LangGraph + FastAPI + Langfuse + pgvector + MCP

> [阿里味] 调研目标已锁定：生产级 Agent Harness 架构，颗粒度拉到"能照着架子直接写代码"。这套组合是 2026 年 AI Native 基础设施的事实标准。

---

## 一、整体架构：为什么这套组合是 2026 年生产级标准

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                       │
│              WebSocket / SSE → Zustand Store 驱动 UI            │
└────────────────────────────┬────────────────────────────────────┘
                             │ Server-Sent Events / WebSocket
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI (ASGI)                            │
│   HTTP REST · WebSocket Manager · SSE Streaming · Auth Middleware │
└────┬──────────────────┬──────────────────────┬─────────────────┘
     │                  │                      │
     ▼                  ▼                      ▼
┌─────────┐      ┌──────────┐          ┌──────────────┐
│LangGraph│      │ Langfuse │          │  MCP Client  │
│ Runtime │      │  SDK     │          │  Registry    │
└────┬────┘      └────┬─────┘          └──────┬───────┘
     │                │                       │
     ▼                ▼                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    PostgreSQL (统一存储层)                     │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│   │  pgvector  │  │ agent_state │  │  关系数据 / 凭证     │   │
│   │  向量存储   │  │ checkpoint  │  │  user · session      │   │
│   └─────────────┘  └─────────────┘  └─────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

**为什么是这套组合？** 每一层各司其职，没有冗余，没有短板：

| 层级 | 技术选型 | 核心职责 | 为什么是它 |
|------|---------|---------|-----------|
| **Agent 运行时** | LangGraph | 多 Agent 状态流、checkpointing、持久化执行 | 2026年事实标准，社区最活跃，DAG+状态机模型碾压同行 |
| **HTTP/WebSocket** | FastAPI | 接口暴露、Streaming、并发管理 | Python 生态最成熟，async-first，和 LangChain 无缝衔接 |
| **可观测性** | Langfuse | trace/span、streaming token 追踪、session 链路 | 对 LangChain/LangGraph 原生支持，开源+自部署，OpenTelemetry 兼容 |
| **统一存储** | PostgreSQL + pgvector | 向量检索 + 关系数据 + agent state | 一个数据库解决所有存储需求，pgvector 性能已碾压纯向量库 |
| **工具标准化** | MCP (Model Context Protocol) | 跨 Agent 工具共享、动态发现、热更新 | USB-C for AI应用，Anthropic 主推，2026年所有主流工具都会 MCP 化 |

---

## 二、LangGraph 层：多 Agent 节点、状态流、Checkpointing

### 状态机 + DAG：Agent 编排的核心模型

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]  # 增量追加，不是覆盖
    current_agent: str                       # 当前负责的 Agent
    session_id: str
    tools_called: list[str]                  # 已调用工具记录（用于防重）
    intermediate_outputs: dict                # Agent 间中间结果
```

### Checkpointing：持久化状态，恢复执行

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

checkpointer = AsyncPostgresSaver.from_conn_string(os.getenv("DATABASE_URL"))

graph = build_agent_graph().compile(
    checkpointer=checkpointer,
    store=store,  # 可选：长期记忆存储（pgvector-backed）
)

config = {
    "configurable": {
        "thread_id": "user_123_session_456",
        "checkpoint_ns": "research_flow_v1",
    }
}

for event in graph.stream({"messages": [("user", user_input)]}, config):
    print(event)
```

---

## 三、FastAPI 层：HTTP/WebSocket、Streaming、Agent 事件流协议

### 整体接口设计

```
POST   /api/v1/agent/run          # 触发 Agent 执行（同步/异步）
GET    /api/v1/agent/stream/{run_id}  # SSE 流式事件
WS     /ws/agent/{session_id}     # WebSocket 双向通道
GET    /api/v1/agent/state/{session_id}  # 查询当前状态
POST   /api/v1/agent/interrupt/{run_id}  # human-in-the-loop 中断
POST   /api/v1/agent/resume/{run_id}     # 从中断点恢复
GET    /api/v1/sessions           # 活跃 session 列表
DELETE /api/v1/sessions/{id}      # 销毁 session
```

### Agent 事件流协议（SSE + WebSocket 共用同一协议）

```python
class AgentEventType(str, Enum):
    # 节点级事件
    AGENT_START = "agent:start"           # Agent 节点开始
    AGENT_END = "agent:end"               # Agent 节点结束
    AGENT_ERROR = "agent:error"           # Agent 执行出错

    # LLM 级事件（用于 token 追踪）
    LLM_TOKEN = "llm:token"               # 流式 token
    LLM_COMPLETE = "llm:complete"         # LLM 响应完成

    # 工具级事件
    TOOL_CALL_START = "tool:call_start"  # 工具开始
    TOOL_CALL_END = "tool:call_end"       # 工具结束
    TOOL_RESULT = "tool:result"           # 工具返回结果

    # 状态级事件
    STATE_UPDATE = "state:update"         # 状态快照更新
    CHECKPOINT_SAVED = "checkpoint:saved" # checkpoint 已保存

    # 会话级事件
    SESSION_END = "session:end"            # 会话正常结束
    SESSION_ABORT = "session:abort"        # 会话被强制终止
```

---

## 四、Langfuse：可观测性——Trace、Span、Streaming Token 追踪

### 为什么是 Langfuse（相比 LangSmith 的优势）

| 维度 | Langfuse | LangSmith |
|------|---------|-----------|
| 部署方式 | 开源自部署 + 云服务 | 仅云服务 |
| 数据主权 | 自己的数据库，完全可控 | 数据在 LangChain 那边 |
| streaming token 追踪 | **原生支持**，token 级延迟分析 | 支持但延迟较高 |
| 价格 | 开源免费（自部署），云服务按量 | 按用量收费，贵 |
| OpenTelemetry | 原生兼容 | 有限支持 |

### Langfuse SDK 集成：装饰器模式

```python
from langfuse.decorators import langfuse_context, observe

@observe(aspect="general")
def researcher_node(state: AgentState, trace=langfuse_context):
    trace.update(
        name="researcher_node",
        metadata={"agent": "researcher", "query": state["messages"][-1]}
    )
    result = researcher_agent.invoke(state)
    trace.generation(
        model="claude-sonnet-4-20250514",
        prompt_tokens=result.usage.prompt_tokens,
        completion_tokens=result.usage.completion_tokens,
        total_tokens=result.usage.total_tokens,
    )
    return result
```

---

## 五、PostgreSQL/pgvector：向量存储 + 关系数据 + Agent State 统一存储

### 为什么是 pgvector 而不是纯向量库（Pinecone/Milvus）

| 维度 | pgvector | Pinecone/Milvus |
|------|---------|----------------|
| 运维复杂度 | 只需运维一个 DB | 需要运维向量库 + 业务 DB，数据同步复杂 |
| 事务支持 | ✅ ACID 完整支持 | ❌ 弱事务，跨库join要靠 ETL |
| agent_state 存储 | ✅ 同库，checkpoint 无缝存储 | ❌ 必须另找地方存 state |
| 关联查询 | ✅ JOIN 向量和关系数据 | ❌ 只能用向量 ID 回查，链路长 |
| 成本 | 一台高配 PG ≈ $200/月 | Pinecone Serverless 按用量，量大了比 PG 贵 |

### 混合检索：向量 + 关键词（pgvector 2025 新功能）

```python
# 搜索记忆：向量相似度 × BM25 关键词权重
async def search_memories(user_id: str, query: str, embedding_model, top_k: int = 5):
    query_embedding = await embedding_model.embed(query)

    results = await pool.fetch("""
        WITH vector_results AS (
            SELECT id, content, metadata,
                   1 - (embedding <=> $1::vector) AS similarity
            FROM vector_memories
            WHERE user_id = $2 AND namespace = $3
            ORDER BY embedding <=> $1::vector LIMIT $4
        ),
        bm25_results AS (
            SELECT id, content, metadata,
                   ts_rank(to_tsvector('chinese', content), plainto_tsquery('chinese', $5)) AS bm25_rank
            FROM vector_memories
            WHERE user_id = $2 AND namespace = $3
            ORDER BY bm25_rank DESC LIMIT $4
        )
        SELECT v.id, v.content, v.metadata, v.similarity,
               COALESCE(b.bm25_rank, 0) AS bm25_rank,
               0.7 * v.similarity + 0.3 * COALESCE(b.bm25_rank, 0) AS hybrid_score
        FROM vector_results v LEFT JOIN bm25_results b USING (id)
        ORDER BY hybrid_score DESC LIMIT $4;
    """, query_embedding, user_id, "default", top_k, query)
    return results
```

---

## 六、MCP（Model Context Protocol）：工具标准化、跨 Agent 工具共享

### MCP 在 Agent Harness 中的定位

```
                    ┌─────────────────────────────┐
                    │   MCP Host (LangGraph 侧)   │
                    │   (MCP Client Manager)       │
                    └──────────┬──────────────────┘
                               │ stdio / Streamable HTTP
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌──────────┐    ┌────────────┐   ┌──────────────┐
        │ MCP Svr: │    │ MCP Svr:   │   │  MCP Svr:    │
        │ FileSystem│    │ PostgreSQL │   │  WebSearch   │
        │ (本地文件)│    │  (数据库)  │   │  (搜索工具)  │
        └──────────┘    └────────────┘   └──────────────┘
```

### LangGraph + MCP 集成

```python
# MCP 工具注册到 LangGraph
def create_mcp_tool_node(mcp_tools: list) -> LangGraphToolNode:
    langchain_tools = [
        convert_mcp_tool_to_langchain(t) for t in mcp_tools
    ]
    return LangGraphToolNode(langchain_tools)

def convert_mcp_tool_to_langchain(mcp_tool: dict):
    from langchain_core.tools import tool

    @tool
    def langchain_wrapper(**kwargs):
        return call_mcp_tool_via_http(mcp_tool["name"], kwargs)

    langchain_wrapper.name = mcp_tool["name"]
    langchain_wrapper.description = mcp_tool["description"]
    return langchain_wrapper
```

---

## 七、Next.js 前端消费：WebSocket/SSE → Zustand 状态驱动

### Zustand Store（状态管理核心）

```typescript
// store/agentStore.ts
interface AgentStore {
  runs: Record<string, AgentRun>;      // run_id → run 状态
  activeRunId: string | null;
  dispatch: (action: { type: string; payload: any; runId: string }) => void;
  setActiveRun: (runId: string) => void;
  resetRun: (runId: string) => void;
}
```

### 事件类型处理

| 事件类型 | 处理逻辑 |
|---------|---------|
| `agent:start` | 更新 `currentNode` |
| `llm:token` | 实时追加到最新 assistant 消息 |
| `tool:call_end` | 追加 tool 消息到 messages |
| `session:end` | 标记 `status: completed` |
| `session:abort` | 标记 `status: aborted` |
| `agent:error` | 标记 `status: error`，记录 error 信息 |

---

## 八、可复用工程模式：项目结构草图

```
agent-harness/
├── docker-compose.yml                  # 一键启动全量基础设施
│
├── backend/                            # FastAPI 主服务
│   ├── agent/
│   │   ├── graph/                     # LangGraph 相关
│   │   │   ├── state.py               # AgentState 定义
│   │   │   ├── nodes/                 # Agent 节点实现
│   │   │   ├── edges/                 # 边和条件路由
│   │   │   ├── graph_builder.py       # 图的组装逻辑
│   │   │   └── checkpoint.py          # Checkpoint 配置
│   │   ├── mcp/                       # MCP 集成
│   │   ├── api/                       # API 路由
│   │   ├── events/                    # 事件协议
│   │   ├── storage/                    # 数据库层
│   │   └── observability/             # 可观测性
│   └── requirements.txt
│
├── mcp-servers/                        # MCP Server 独立进程
│   ├── search_server/
│   ├── code_server/
│   └── memory_server/
│
├── frontend/                           # Next.js 前端
│   ├── components/
│   │   ├── ChatPanel.tsx
│   │   ├── AgentTimeline.tsx          # 节点执行可视化
│   │   └── TokenUsage.tsx
│   ├── store/agentStore.ts             # Zustand store
│   └── lib/agentEvents.ts              # SSE/WebSocket 消费
│
└── infra/
    ├── postgres/init.sql              # schema 初始化
    └── nginx/streaming.conf
```

---

## 九、架构自检清单（生产上线前必过）

```
┌──────────────────────────────────────────────────────────┐
│           生产上线自检 · Agent Harness 架构              │
├────────────────────┬────────────────────────────────────┤
│ LangGraph          │ [ ] Checkpoint 恢复验证过吗？        │
│                    │ [ ] astream / astream_events 区分清？ │
│                    │ [ ] 节点重入幂等吗？                  │
├────────────────────┼────────────────────────────────────┤
│ FastAPI            │ [ ] WebSocket 重连逻辑做了吗？        │
│                    │ [ ] SSE disconnect 清理资源吗？      │
│                    │ [ ] 并发上限限流了吗？                │
├────────────────────┼────────────────────────────────────┤
│ Langfuse           │ [ ] streaming token 不丢？          │
│                    │ [ ] PII 脱敏了吗？                    │
│                    │ [ ] 告警阈值设了吗？                   │
├────────────────────┼────────────────────────────────────┤
│ PostgreSQL/pgvector│ [ ] HNSW 索引建了吗？                 │
│                    │ [ ] 连接池上限配了吗？                 │
│                    │ [ ] checkpoint 过期清理策略了吗？     │
├────────────────────┼────────────────────────────────────┤
│ MCP                │ [ ] 工具超时控制了吗？                │
│                    │ [ ] 工具失败降级方案有吗？             │
│                    │ [ ] 新增 tool 后 graph 怎么热更新？   │
└────────────────────┴────────────────────────────────────┘
```
