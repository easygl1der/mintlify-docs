---
title: claw-code 调研：Claude Code 底层 Harness 结构解析
description: 169k stars，Rust 实现，9/9 bash validation，40 工具完整实现，Session 持久化，Mock parity harness
---

# claw-code 调研：Claude Code 底层 Harness 结构解析

> [阿里味] 调研目标明确：理解 Claude Code 的底层 harness 架构是怎么组织的。claw-code 是目前已知最完整的 Claude Code 开源复刻——169k stars、史上最快破 10 万 star 的 repo，Rust 实现，Python porting workspace 并行。**闭环**：读完源码、拉通结构、写进笔记。

---

## 一、项目定性：这不是一个"项目"，是一个"系统"

claw-code 有两层含义：

**表层**：一个 169k stars 的开源项目，Rust 重写了 Claude Code 的 CLI 工具链，包含 api client、tool system、session persistence、permission enforcement、MCP lifecycle 等核心模块。

**深层**：它是一个** autonomous claw workflows 驱动的自维护仓库**——仓库本身由 lobsters/claws（ autonomous coding agents）通过 `oh-my-codex` 驱动，不是人类在手动维护代码。人类只给方向，claws 执行、测试、恢复、推送。

核心哲学（PHILOSOPHY.md 原话）：

> **humans set direction; claws perform the labor.**

---

## 二、技术栈与数据

```
语言：Rust（约 20K 行）+ Python（porting workspace）
stars：169,357（2026-04）
forks：102,834
历史地位：史上最快破 10 万 stars 的 repo（2 小时）
构建工具：oh-my-codex（OmX）
CLI 名字：claw（对标 claude）
默认模型：claude-opus-4-6
```

---

## 三、Rust workspace：9 个 crate 的职责划分

```
rust/
├── crates/
│   ├── api/                    # Anthropic API client + SSE streaming
│   ├── commands/               # 斜杠命令注册表（/help, /status, /compact 等）
│   ├── compat-harness/         # 从上游 TS 源码提取 tool/prompt manifest 的 harness
│   ├── mock-anthropic-service/ # 确定性 mock，用于 CLI parity test
│   ├── plugins/                # 插件元数据、hook 集成
│   ├── runtime/                # 核心：ConversationRuntime、权限、session、MCP、prompt assembly
│   ├── rusty-claude-cli/       # CLI binary：REPL、streaming 渲染、工具调用展示
│   ├── telemetry/               # Session trace events + 使用量 telemetry
│   └── tools/                  # 工具实现：Bash、ReadFile、WriteFile、Glob、Grep、WebSearch、WebFetch、Agent、Todo、Task*、Team* 等
```

**每个 crate 的核心导出（runtime/lib.rs）**：

| crate | 核心职责 |
|-------|---------|
| `api` | HTTP client、SSE 流解析、OAuth bearer、request/response types |
| `runtime` | ConversationRuntime（核心循环）、Session 持久化、权限策略、MCP client、system prompt assembly |
| `tools` | 40 个工具的完整实现：bash/file/grep/glob/web/task/team/LSP/MCP/Notebook/Skill 等 |
| `commands` | 斜杠命令定义和 help 生成 |
| `plugins` | 插件 metadata、hook 集成表面 |
| `telemetry` | Session trace event 类型、使用量记录 |
| `mock-anthropic-service` | `/v1/messages` 端点的确定性 mock，用于 parity test |

---

## 四、runtime 核心模块：真正值得扒的

### 4.1 会话与循环
- **`session`**：Session 持久化（`.claw/sessions/`）
- **`conversation`**：`ConversationRuntime`——这是核心 agentic loop，驱动交互和一次触发
- **`session_control`**：会话控制
- **`compact`**：会话压缩（token 节约）

### 4.2 权限与安全
- **`permissions`**：权限模型（read-only / workspace-write / danger-full-access）
- **`permission_enforcer`**：跨所有工具的权限执行
- **`sandbox`**：沙箱隔离
- **`policy_engine`**：策略引擎
- **`trust_resolver`**：信任解析

### 4.3 工具执行
- **`bash`** + **`bash_validation`**（9 个 submodule）：
  - `sedValidation`、`pathValidation`、`readOnlyValidation`
  - `destructiveCommandWarning`、`commandSemantics`、`bashPermissions`
  - `bashSecurity`、`modeValidation`、`shouldUseSandbox`
- **`file_ops`**：ReadFile、WriteFile、EditFile、GlobSearch、GrepSearch
- **`static_tool_executor`**：静态工具执行器

### 4.4 MCP（Model Context Protocol）
- **`mcp_client`**：MCP client transport（Stdio / WebSocket / HTTP）
- **`mcp_lifecycle_hardened`**：MCP server 生命周期管理（hardened 版本）
- **`mcp_tool_bridge`**：MCP 工具桥接到 CLI 工具系统
- **`mcp_stdio`**：MCP stdio transport 实现

### 4.5 Hook 系统
- **`hooks`**：`HookRunner`、`HookEvent`、`HookProgressEvent`、`HookAbortSignal`
- **`plugin_lifecycle`**：插件生命周期管理

### 4.6 恢复与自愈
- **`recovery_recipes`**：恢复配方
- **`stale_branch`**：陈旧分支处理

---

## 五、工具系统：40 个工具，9/9 bash validation 完成

### 工具分类（从 PARITY.md）：

| 类别 | 工具 |
|------|------|
| **文件操作** | read_file、write_file、edit_file、glob_search、grep_search |
| **bash** | Bash（9 validation submodule 全完成）|
| **Web** | WebSearch、WebFetch |
| **任务管理** | TaskCreate、TaskGet、TaskList、TaskStop、TaskUpdate、TaskOutput |
| **多 Agent** | Agent（子 agent 委托）、TeamCreate、TeamDelete、CronCreate、CronDelete、CronList |
| **LSP** | LSP（诊断、hover、定义、引用、补全、格式化、symbols）|
| **MCP** | ListMcpResources、ReadMcpResource、MCP（工具调用桥接）|
| **Notebook** | NotebookEdit |
| **其他** | TodoWrite、Skill、ToolSearch、Sleep、SendUserMessage/Brief、Config、EnterPlanMode、ExitPlanMode、StructuredOutput、REPL、PowerShell |

### Bash 9 validation submodules（全部完成）：

```
bash validation submodules
├── sedValidation         — sed 命令执行前验证
├── pathValidation         — 命令中文件路径验证
├── readOnlyValidation    — read-only 模式下阻止写入
├── destructiveCommandWarning — rm -rf 等危险命令告警
├── commandSemantics      — 命令意图分类
├── bashPermissions       — 按命令类型权限门控
├── bashSecurity          — 安全检查
├── modeValidation        — 当前权限模式验证
└── shouldUseSandbox      — 沙箱决策逻辑
```

---

## 六、权限系统：三级模式 + 跨工具强制执行

```
read-only              — 不能写任何文件
workspace-write        — 只能写当前 workspace
danger-full-access     — 全部允许（默认）
```

权限在 `permission_enforcer` 层强制执行，跨所有工具生效，不只是 bash。

---

## 七、MCP 生命周期：完整覆盖

从 `PARITY.md` 看，MCP 覆盖了完整生命周期：

- [x] MCP server 连接
- [x] 列出 MCP tools（`ListMcpResources`）
- [x] 读取 MCP resources（`ReadMcpResource`）
- [x] 调用 MCP tool（`MCP` bridge）
- [x] 断开连接

MCP client transport 支持三种：Stdio、WebSocket、HTTP（managed proxy）。

---

## 八、和 LangGraph harness 的本质对比

| 维度 | claw-code (Claude Code harness) | LangGraph harness |
|------|--------------------------------|-------------------|
| **核心抽象** | ConversationRuntime + tool dispatcher | StateGraph（DAG 状态机）|
| **状态持久化** | Session 持久化（文件）| PostgresSaver checkpoint |
| **工具系统** | 40 工具，内置 9 种 bash validation | LangChain Tools + MCP |
| **多 Agent** | Agent tool（子 agent）+ Team* Cron* | Subgraph + Send 并行 |
| **权限模型** | 三级模式（read-only/workspace-write/danger-full）| 无内置（需自行实现）|
| **harness 测试** | Mock parity harness 完整 CLI 测试 | 无标准化 harness 测试框架 |
| **语言** | Rust（~20K LOC）| Python |
| **维护方式** | Autonomous claw workflows（oh-my-codex）| 社区维护 |

**关键洞察**：Claude Code harness 的设计哲学是**把安全和权限做进 harness 层**，而不是让 agent 自己判断。LangGraph 则把编排和状态流做进 harness 层，权限安全不在它的范畴。

这两个思路实际上可以组合：用 LangGraph 做编排层，用 claw-code 的权限模型做安全层。

---

## Source

- GitHub: https://github.com/ultraworkers/claw-code
