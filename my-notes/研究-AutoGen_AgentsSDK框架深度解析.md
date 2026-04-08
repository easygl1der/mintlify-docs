---
title: AutoGen vs OpenAI Agents SDK：框架调研深度解析
description: GroupChat、ConversationalAgent、Core三层架构 vs Handoff、Guardrails、Session
---

# AutoGen vs OpenAI Agents SDK：框架调研深度解析

---

## 一、AutoGen：微软出品的多 Agent 旗舰框架

### 1.1 核心概念

AutoGen 是微软开源的多 Agent 开发框架，GitHub **56.7k stars**（截至 2026 年初），是当前多 Agent 领域 star 最多的开源项目。

AutoGen 的架构分三层：

**Core 层（底层）**
事件驱动的消息传递框架，负责 Agent 之间的异步通信。Core 层不做任何 AI 假设——它只是一个通用的多 Agent 运行时。Python 3.10+。

**AgentChat 层（快速原型）**
建立在 Core 之上的高阶 API，目标是在 5 行代码内跑通一个多 Agent 对话。核心组件：
- `ConversationalAgent`：带对话历史的单 Agent，支持系统提示 + 工具
- `GroupChat`：多 Agent 共享同一对话空间，Agent 们轮流发言
- `GroupChatManager`：GroupChat 的控制器——决定下一个谁说话、什么时候终止

**Extensions 层（扩展能力）**
对接外部服务：MCP 服务器、Docker 代码执行器、gRPC 分布式 Agent、Assistant API 等。

### 1.2 GroupChatManager 机制——AutoGen 最核心的设计

GroupChatManager 解决的是一个根本问题：**多 Agent 协作时，谁说了算？**

机制：
1. 创建一个 `GroupChat`，把多个 `ConversationalAgent` 加进去
2. 创建一个 `GroupChatManager`，持有这个 GroupChat
3. 用户发一条消息 → GroupChatManager 决定**哪个 Agent 接下来处理**
4. Agent 处理完 → 消息写回 GroupChat → Manager 决定下一个
5. 如此循环，直到满足终止条件

**SelectSpeaker 策略**：默认是"让 LLM 自己决定下一个谁来"——Manager 会问"现在谁最适合处理这个问题？"

### 1.3 与 LangGraph 的本质差异

| 维度 | AutoGen | LangGraph |
|------|---------|-----------|
| **核心抽象** | 对话（Conversation） | 有向图（Graph） |
| **状态管理** | 对话历史（chat history） | 显式 StateGraph，每条边可带条件 |
| **执行模型** | 动态路由——Manager 决定下一个 Agent | 静态图——你定义好每条边的条件，执行时按图走 |
| **持久化** | 无内置持久化（内存对话） | Checkpointing——任意节点可暂停/恢复 |

**本质差异一句话**：AutoGen 的隐含假设是"Agent 在对话"，状态在对话历史里；LangGraph 的隐含假设是"Agent 在执行工作流"，状态在 StateGraph 里。

**AutoGen 适合模拟一群人开会，LangGraph 适合编排一条工厂流水线。**

### 1.4 重要信号：微软战略转移

⚠️ AutoGen 官方面网站上现在写明：**"recommend new users check out Microsoft Agent Framework"**，AutoGen 本身只保证接收 bug fix 和安全补丁，不再是微软的 active 主推项目。

---

## 二、OpenAI Agents SDK：2026 年官方多 Agent SDK

### 2.1 定位与发布时间

OpenAI 在 2025 年初正式发布 `openai-agents-python` SDK（GitHub **20.6k stars**），定位是**轻量、官方、够用就好**。

### 2.2 核心概念

**Agents**：配置好的 LLM 实例——.instructions（系统提示）+ .tools（工具列表）+ .guardrails（护栏）+ .handoffs（交接）

**Tools**：三类工具——Python 函数（Function）、MCP 工具、Hosted Tools（OpenAI 托管的搜索、代码执行等）

**Guardrails**：输入输出校验——在 LLM 前后各有一道检查，可以拒绝或修正不符合要求的内容。

**Sessions**：自动管理多轮对话历史，不用手动维护 messages 列表。

### 2.3 Handoffs 机制——OpenAI Agents SDK 最独特的设计

Handoffs 是 Agents SDK 的核心创新：**让一个 Agent 把任务完整地转交给另一个 Agent，包含对话上下文**。

```python
pdf_agent = Agent(name="pdf_reader", instructions="你是PDF专家", tools=[...])
qa_agent = Agent(name="qa", instructions="你负责问答", handoffs=[pdf_agent])

# qa_agent 发现需要读 PDF → handoff 到 pdf_agent
# pdf_agent 完成 → 回到 qa_agent 继续
```

**和 AutoGen GroupChatManager 的本质区别**：
- AutoGen：Manager 决定下一个谁来，所有 Agent 共享同一个消息池（广播模式）
- OpenAI Agents SDK：Handoff 是**完全交接**——A 把控制权完整交给 B，B 完成后回到 A（栈式调用）

**Handoff 更适合线性任务流**（PDF 读 → 问答 → 输出），**GroupChat 更适合需要多方同时参与的协作场景**。

---

## 三、四框架横向对比（2026 年数据）

```
┌──────────────┬───────────────┬───────────────┬──────────────┬──────────────────┐
│              │   AutoGen     │ OpenAI Agents │   LangGraph  │     CrewAI       │
├──────────────┼───────────────┼───────────────┼──────────────┼──────────────────┤
│ GitHub Stars │    56.7k     │    20.6k      │    28.5k    │     48.1k        │
├──────────────┼───────────────┼───────────────┼──────────────┼──────────────────┤
│ 核心抽象     │   对话+Manager │   Agent+Handoff│   StateGraph │  Agent+Task+Crew │
├──────────────┼───────────────┼───────────────┼──────────────┼──────────────────┤
│ 多 Agent     │  GroupChat    │   Handoff     │  Subgraph    │   Crew(层次化)   │
│ 协作模型     │  (广播+仲裁)   │  (栈式交接)   │  (图节点)    │                  │
├──────────────┼───────────────┼───────────────┼──────────────┼──────────────────┤
│ 状态持久化   │     无        │    Session    │  Checkpoint  │   Memory+Knowledge│
├──────────────┼───────────────┼───────────────┼──────────────┼──────────────────┤
│ 工具调用     │ 函数+MCP+Docker│ 函数+MCP+Hosted│  函数+LangChain│ 函数+MCP+内置   │
├──────────────┼───────────────┼───────────────┼──────────────┼──────────────────┤
│ 维护状态     │  维护模式(⚠️) │    Active     │    Active    │     Active       │
└──────────────┴───────────────┴───────────────┴──────────────┴──────────────────┘
```

---

## 四、生产级落地现状

| 框架 | 生产案例 | 维护状态 |
|------|---------|---------|
| **AutoGen** | Microsoft Copilot Studio 底层、Magentic-One、Airbus、IBM | ⚠️ 维护模式 |
| **OpenAI Agents SDK** | 2026 年新项目首选，OpenAI 自己用它做 GPT-4o 的 Agent 能力验证 | Active |
| **LangGraph** | 生产项目最广泛，数千个生产部署案例 | Active |
| **CrewAI** | 最快上手，团队学习成本低 | Active |
