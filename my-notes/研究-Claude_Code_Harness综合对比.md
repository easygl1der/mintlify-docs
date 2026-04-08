---
title: Claude Code Harness vs 普通 AI 对话框：综合对比与选型指南
description: 核心架构优势、十大痛点对比、SWE-bench 数据、选型决策树
---

# Claude Code Harness vs 普通 AI 对话框：综合对比与选型指南

> [阿里味] 四个 agent 并行调研完毕，颗粒度拉满。本综合结论不是四份笔记的拼接，是**端到端的选型决策指南**——什么时候用 harness、什么时候用对话框、为什么差距是结构性的。

---

## 一、先说结论

**普通对话框和 Claude Code harness 的差距，不是体验差异，是结构性差异。**

同样的 LLM，放进 harness 里跑 SWE-bench 能完成 **76.8%** 的软件工程任务；放在对话框里，连评测资格都没有——因为它无法执行文件操作和 bash 命令。

这不是 AI 模型能力的问题，是**执行环境**的问题。

---

## 二、八维度量化对比

```
┌─────────────────────┬──────────────────────────────┬──────────────────────────────┐
│ 维度                │ Claude Code Harness          │ 普通 AI 对话框               │
├─────────────────────┼──────────────────────────────┼──────────────────────────────┤
│ 上下文持久化         │ Session 文件持久化，可中断恢复  │ 刷新即丢失                    │
│ 工具调用精度         │ 40 工具确定性 dispatch        │ 纯推理，无校验                │
│ 多步骤任务           │ ConversationRuntime + 状态管理  │ 单轮推理，上下文随步数衰减     │
│ 文件系统安全         │ 三级权限 + sandbox + pathValidation │ 无法安全操作文件           │
│ Bash 执行           │ 9 validation submodule，把关    │ 完全无法执行                  │
│ 错误恢复            │ recovery_recipes + checkpoint  │ 用户手动重述，重复犯错        │
│ Long Running 任务    │ TaskRegistry 后台并行          │ 同步等待，60-120s 超时        │
│ 任务完成率           │ 65-76.8%（SWE-bench 实测）   │ 无数据（无法完成这些任务）     │
└─────────────────────┴──────────────────────────────┴──────────────────────────────┘
```

---

## 三、核心架构差异：本质在哪

### 对话框的抽象：单轮语言生成

```
[User Input] → [LLM] → [Text Output]
              ↑____无状态单轮____↓
```

**局限**：只能推理，不能执行。上下文窗口是唯一的状态存储，窗口关闭一切归零。

### Harness 的抽象：持久化的工作环境

```
[User Input] → [ConversationRuntime] → [Tool Dispatcher] → [执行系统]
                    ↑                       ↑
               [Session 持久化]        [Permission Enforcer]
                    ↑
              [Compact 压缩]
```

**能力**：工具是 first-class citizen，系统操作不是"AI 描述的操作"，是 **harness 直接执行**。

---

## 四、Claude Code 的十大核心优势

### 1. 工具系统：40 个 Rust 实现的 first-class 工具

| 类别 | 工具 | 对话框能做什么 |
|------|------|--------------|
| 文件操作 | Read/Write/Edit/Glob/Grep | 只能复述，无法操作 |
| Bash | 执行任意 shell 命令 | 完全无法执行 |
| Web | Search + Fetch | 能搜但不能自动化 |
| 任务管理 | TaskCreate/Get/List/Stop | 没有这个概念 |
| 多 Agent | Agent tool + Team* | 单线程，没有协作 |
| MCP | 完整生命周期支持 | 不支持 |

### 2. 权限系统：三级门控，AI 无法绕过

```
read-only → workspace-write → danger-full-access
```

权限在 `permission_enforcer` 层**强制执行**，不是 prompt 里说"请不要删文件"。

### 3. Bash 9 validation submodule

```
sedValidation | pathValidation | readOnlyValidation
destructiveCommandWarning | commandSemantics | bashPermissions
bashSecurity | modeValidation | shouldUseSandbox
```
每条都是**确定性规则**，不是 AI 判断。

### 4. Session 持久化：跨会话上下文

`.claw/sessions/` 文件 checkpoint，调试到一半刷新页面？直接 resume。明天继续项目？Session 恢复。

### 5. 多 Agent 协作：Agent tool + Team*

主 agent 拆分任务，子 agent 并行执行，结果汇总。**不是开三个对话框各自为战**，是真正的多线程协作。

### 6. 会话压缩（compact）：防止上下文膨胀

保留策略：最近对话完整 + 早期摘要 + 关键工具结果 + CLAUDE.md 完整保留。

### 7. CLAUDE.md 项目记忆：让 AI "懂行"

三层持久化：
- `CLAUDE.md`（全局规范）
- `.claude/rules/`（按文件类型按需加载）
- `auto memory`（AI 主动积累的调试笔记）

### 8. 错误恢复：recovery_recipes + checkpoint

`FailureScenario` 枚举 + `EscalationPolicy` 分级处理。不是用户重新描述问题，是 **harness 根据失败类型自动匹配恢复策略**。

### 9. 五档 Permission Mode

| 模式 | 场景 |
|------|------|
| `default` | 审计代码，只读 |
| `acceptEdits` | 迭代开发，不需每次确认 |
| `plan` | 大改动前的方案设计 |
| `auto` | 长任务，减少弹窗疲劳（含分类器） |
| `dontAsk` | CI 管道，白名单工具 |

### 10. 验证闭环：承诺的结果用证据交付

AI 说"已修复"？**必须贴出 `npm test` 的 `PASS` 输出**，才叫闭环。语言声明不算。

---

## 五、解决的痛点：十个具体场景

| 痛点 | 对话框的处理 | Harness 的闭环 |
|------|------------|--------------|
| 写代码无法执行 | 给建议，不负责结果 | Bash 跑测试，PASS 才闭环 |
| 文件操作风险 | 黑盒操作，错了不知道 | diff 可视 + sandbox 权限隔离 |
| 上下文丢失 | 刷新全丢 | Session 持久化，跨端恢复 |
| 多步骤工作流 | 一步一问，上下文衰减 | 工具链串联 + CLAUDE.md 全程约束 |
| 权限安全问题 | 全信任无兜底 | 最小权限，危险操作必须显式授权 |
| 多 Agent 协作 | 单兵排队 | Team* 并行，结果自动汇合 |
| Long Running 任务 | 同步阻塞，超时中断 | 异步后台，CI 集成 |
| 项目规范 | 每次重新注入 | CLAUDE.md 持久生效 |
| 跨会话记忆 | 无 | auto memory 主动积累 |
| 验证闭环 | "已修复"是语言声明 | 输出 npm test PASS 证据 |

---

## 六、什么时候选 Harness，什么时候选对话框

| 场景 | 推荐 | 原因 |
|------|------|------|
| 简单问答、知识查询 | 对话框 | Harness 复杂度是浪费 |
| 单轮代码片段生成 | 对话框 | 上下文简单，无优势 |
| **多步骤代码修改** | **Harness** | 文件操作+命令执行+测试验证，缺一不可 |
| **Bug 修复 + 验证** | **Harness** | 需要运行测试确认修复 |
| **代码库探索** | **Harness** | glob/grep/read_file 确定性操作 |
| **自动化 workflow（10+ 步骤）** | **Harness** | 没有 harness 完成率趋近于零 |
| 需要安全的文件操作 | **Harness** | 权限+沙箱是对话框不具备的 |

---

## 七、SWE-bench 榜单对标

SWE-bench 是最权威的软件工程任务 benchmark，所有可衡量的任务完成率**全部来自 harness 环境**：

| 模型/Agent | SWE-bench 成绩 |
|-----------|--------------|
| mini-SWE-agent v2.0.0 + Claude 4.5 Opus | **76.8%** |
| mini-SWE-agent v2.0.0 + Gemini 3 Flash | **75.8%** |

对话框没有公开数据的原因：
1. 无法定义公平对比——根本不支持文件操作和命令执行
2. 无法跑同样的测试用例集
3. 无法自动化评测（harness 的确定性执行环境是对话框没有的）

**结论**：离开了 harness，连评测资格都没有。

---

## 八、综合选型决策树

```
任务是否需要执行操作（文件/命令/测试）？
├── 否 → 普通对话框（简单问答、知识查询）
└── 是 ↓
  任务是否需要多步骤（>3步）？
  ├── 否 → 可以用对话框，但 harness 效率更高
  └── 是 ↓
    是否需要安全的文件操作？
    ├── 是 → 必须用 Harness（权限+沙箱是对话框没有的）
    └── 否 ↓
      是否需要跨会话持久化？
      ├── 是 → 必须用 Harness（Session 持久化是对话框没有的）
      └── 否 ↓
        是否需要多 Agent 协作？
        ├── 是 → 必须用 Harness（Team* 是对话框没有的）
        └── 否 → Harness 仍然更优（工具调用精度 + 验证闭环）
```

---

## Sources

- [claw-code (ultraworkers)](https://github.com/ultraworkers/claw-code) — 169k stars，Rust 实现
- [SWE-agent SWE-bench](https://github.com/princeton-nlp/SWE-agent) — 65-76.8% 任务完成率
