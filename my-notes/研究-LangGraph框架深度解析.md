---
title: LangGraph 框架调研：多 Agent 编排的事实标准
description: StateGraph、Checkpointing、Human-in-the-loop、Streaming、PostgresSaver、生产级架构
---

# LangGraph 框架调研：多 Agent 编排的事实标准

## 一句话定性

LangGraph 是 2026 年多 Agent 生态里最底层、最工程化、最能打的编排框架。它的定位是"比 LangChain 低一层的精细化控制层"——不封装，给够自由度；不简陋，checkpointing / human-in-the-loop / streaming 全都原生支持。28.5k GitHub stars、491 个 releases、2026 年 4 月刚发 v1.1.6，活跃度拉满。

---

## 一、核心概念拆解

### 1.1 StateGraph——图的本体

StateGraph 是 LangGraph 的核心 API，底层逻辑是 Pregel/Apache Beam 的计算模型 + NetworkX 的接口风格。状态用 TypedDict 定义，每个节点是一个 `(State) -> Partial<State>` 签名的函数，返回对状态的增量更新。

```python
from langgraph.graph import START, StateGraph
from typing_extensions import TypedDict

class State(TypedDict):
    text: str
    turns: int

def node_a(state: State) -> dict:
    return {"text": state["text"] + "a", "turns": state["turns"] + 1}

graph = StateGraph(State)
graph.add_node("node_a", node_a)
graph.add_edge(START, "node_a")
graph.add_edge("node_a", END)

compiled = graph.compile()
result = compiled.invoke({"text": "", "turns": 0})
# result → {'text': 'a', 'turns': 1}
```

**为什么这样设计**：状态是共享的，所有节点都对同一个状态对象读写。返回值是 `dict`（Partial<State>），LangGraph 会自动把节点输出 merge 到主状态——这个 merge 逻辑叫 **ChannelWrite**，是 LangGraph 持久化的原子单元。

### 1.2 Checkpointing——状态持久化的底层逻辑

Checkpoint 是 LangGraph 的核心创新点之一。它在图的每个"超步"（superstep）之间自动保存状态快照，使得：

- workflow 可以 **暂停**（interrupt）
- 可以 **恢复**（resume from last checkpoint）
- 可以 **重放**（replay from specific checkpoint）

Checkpoint 接口定义了五个原子操作：

| 方法 | 同步 | 异步 | 语义 |
|------|------|------|------|
| `put` | ✅ | ✅ | 写入一个 checkpoint + 元数据 |
| `get_tuple` | ✅ | ✅ | 按 config（thread_id）读取单个 checkpoint |
| `list` | ✅ | ✅ | 列出所有匹配的 checkpoint |
| `put_writes` | ✅ | ✅ | 写入"待定写入"（中断期间的人工干预） |
| `delete_thread` | ✅ | ✅ | 删除某 thread 的所有 checkpoint |

```python
# 同步 Postgres checkpoint
from langgraph.checkpoint.postgres import PostgresSaver

with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()  # 创建表（幂等，重复调用安全）
    checkpointer.put(write_config, checkpoint, {}, {})

# 异步版本
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
    await checkpointer.aput(write_config, checkpoint, {}, {})
```

**thread_id** 是 checkpoint 的核心维度——每个用户对话、每个独立任务线程，都对应一个 thread_id。

### 1.3 Human-in-the-Loop——中断与干预

LangGraph 的 interrupt 分两种：

1. **Graph 级别 interrupt**：`graph.compile(interrupt_before=["node_name"])` 会在指定节点执行前暂停
2. **Node 级别 interrupt**：在节点函数内部调用 `Command(resume={"..."})` 主动交出控制权

Human-in-the-loop 的典型流程：
```
Agent 执行 → interrupt at 审批节点 → 人类查看状态 → approve/reject → graph 恢复执行
```

### 1.4 Token Streaming

LangGraph 的 stream 方法按事件类型 yield，内容是 JSON-serializable 的 dict：

```python
# stream_mode="updates"：每个节点的增量输出
for event in compiled.stream({"text": ""}, stream_mode="updates"):
    print(event)  # {"node_a": {"text": "a", "turns": 1}}

# stream_mode="values"：每个超步后的完整状态快照
for event in compiled.stream({"text": ""}, stream_mode="values"):
    print(event)  # 当前完整状态
```

---

## 二、多 Agent 协作模式

### 2.1 节点设计——用共享状态做 Agent 间通信

LangGraph 没有"Agent"这个抽象——一切都是节点。Agent 之间的通信靠读写同一个状态对象。

### 2.2 条件跳转——add_conditional_edges

```python
def route_after_note(state: AgentState) -> str:
    if "搜索" in state["user_input"] or "查" in state["user_input"]:
        return "searcher"
    elif "导航" in state["user_input"] or "去" in state["user_input"]:
        return "navigator"
    else:
        return END

graph.add_conditional_edges(
    "note_taker",
    route_after_note,
    {"searcher": "searcher", "navigator": "navigator", END: END}
)
```

### 2.3 Supervisor 模式——多 Agent 编排的高层抽象

LangGraph 推荐的多 Agent 协作模式是 **Supervisor**——一个专门负责"决定下一个谁来"的节点，其他 Agent 都是叶子节点。

### 2.4 Send——跨节点即时消息传递

```python
from langgraph.constants import Send

def spawn_parallel_searches(state: AgentState) -> list[Send]:
    queries = state["user_input"].split("|")
    return [Send("searcher", {"query": q}) for q in queries]

graph.add_conditional_edges(START, spawn_parallel_searches)
```

---

## 三、与前端配合的接口协议设计

### HTTP/WebSocket 协议设计思路

**短任务**（请求-响应）：`graph.invoke()` 同步调用，FastAPI 返回 JSON

**长任务**（streaming）：
- **Server-Sent Events（SSE）**：实现简单，单向推送，适合纯文本流
- **WebSocket**：双向通信，可以接收前端的"approve/reject"信号再恢复 graph

### Streaming 事件协议

```python
# stream_mode="updates"：每个节点的增量输出
{"node_name": {"key": "value"}}

# stream_mode="values"：每个超步后的完整状态快照
{"user_input": "...", "search_results": [...], "turns": 3}

# stream_mode="debug"：包含 checkpoint 元数据的调试信息
{"type": "checkpoint", "config": {...}, "state": {...}}
```

---

## 四、生产级完整架构

```
[Next.js 前端]
      ↕ SSE / WebSocket
[FastAPI 网关层]
      ↕
[LangGraph 核心编排层]
  ├── StateGraph（业务流程）
  ├── Pregel（执行引擎）
  ├── Checkpointer（PostgresSaver）
  └── Tool Executor（MCP 协议）
      ↕
[Langfuse（可观测性）] ← traces + metrics
      ↕
[PostgreSQL + pgvector（状态持久化 + 向量检索）]
      ↕
[MCP Tools（PDF 解析 / 文件系统 / API 调用）]
```

---

## 五、GitHub 活跃度

| 指标 | 数据 |
|------|------|
| Stars | 28.5k |
| Forks | 4.9k |
| Watchers | 148 |
| Commits | 6,699 |
| Releases | 491（最新 v1.1.6，2026-04-03） |

**趋势判断**：
- 491 个 releases 说明发布节奏极快（平均不到 1.5 天一个版本）
- v1.1.6 在 2026 年 4 月刚发，说明项目在持续维护
- 28.5k stars 在 GitHub 整个 AI Agent 领域排名第一档

---

## 六、与"PDF阅读+AI问答+IDE式多面板工作台"场景的契合点

| 需求 | LangGraph 解法 |
|------|---------------|
| PDF 解析 + QA 多步骤 | StateGraph，PDF 节点 → 解析节点 → QA 节点 → 展示节点 |
| 状态跨页面持久化 | PostgresSaver，thread_id = session_id，刷新页面不丢状态 |
| IDE 多面板实时更新 | SSE/WebSocket streaming，stream_mode="updates" 按节点推送 |
| human-in-the-loop | graph.compile(interrupt_before=["confirm_delete"])，危险操作需人工确认 |
| 对话历史长期记忆 | checkpoint 持久化到 Postgres，同时往 pgvector 写摘要向量做 RAG |

**LangGraph 适配度**：⭐⭐⭐⭐⭐（满分）

---

## 七、竞品一句话对比

| 框架 | 定位 | 多 Agent | 状态持久化 | Streaming | 上手难度 |
|------|------|----------|-----------|-----------|---------|
| **LangGraph** | 底层精细化编排 | 状态共享+条件边 | PostgresSaver 原生 | SSE/WebSocket | 中（需要理解 graph 模型） |
| **AutoGen** | 对等 Agent 协作 | 独立 Agent + 消息 | 不支持 | 原生 | 低（对话式） |
| **CrewAI** | 任务导向编排 | Task+Role 抽象 | 不支持 | 支持 | 低（Role 概念直观） |
| **OpenAI Agents SDK** | 轻量级工具调用 | 极简 | 不支持 | 支持 | 最低（几行代码） |
