---
title: Prismer 协作功能
description: vs. Overleaf 功能对比分析
---

# Prismer 协作功能

## 功能对比矩阵

### vs. Overleaf

| 功能维度 | Overleaf | Prismer | 差距 |
|----------|----------|---------|------|
| **实时协作** | | | |
| 实时光标共享 | ✅ | ❌ | -100% |
| 用户在线状态 | ✅ | ❌ | -100% |
| 文本内联评论 | ✅ | ❌ | -100% |
| 变更追踪 | ✅ | ❌ | -100% |
| 多用户 LaTeX 编辑 | ✅ | ❌ | -100% |
| **版本控制** | | | |
| 完整版本历史 | ✅ | ⚠️ 部分 | -50% |
| 版本对比 | ✅ | ❌ | -100% |
| 回滚功能 | ✅ | ❌ | -100% |
| **项目管理** | | | |
| 模板库 | ✅ | ✅ | 0% |
| 图表管理 | ✅ | ⚠️ 有限 | -30% |
| 参考文献管理 | ✅ | ⚠️ 手动 | -40% |
| **AI 辅助** | | | |
| AI 补全 | ⚠️ 有限 | ✅ 深度 | +50% |
| AI 写作助手 | ⚠️ 有限 | ✅ 完整 | +50% |
| 语法检查 | ✅ | ❌ | -100% |
| **代码执行** | | | |
| Jupyter 集成 | ❌ | ✅ | +100% |
| 代码块执行 | ❌ | ✅ | +100% |
| **形式化验证** | | | |
| Lean/Coq/Z3 | ❌ | ✅ | +100% |

## Prismer 协作功能现状

### 支持的功能

#### 1. IM 消息系统

**消息类型**:
| 类型 | 描述 | 支持 |
|------|------|------|
| Agent ↔ Human | Agent 与用户对话 | ✅ |
| Human ↔ Human | 用户间私信 | ✅ |
| Group Chat | 群组讨论 | ✅ |
| @mention | 提及通知 | ❌ |

#### 2. Workspace 参与者角色

| 角色 | 创建工作区 | 编辑内容 | 运行 Agent | 管理成员 |
|------|-----------|----------|------------|----------|
| **owner** | ✅ | ✅ | ✅ | ✅ |
| **member** | ❌ | ✅ | ✅ | ❌ |
| **agent** | ❌ | ✅ | ✅ | ❌ |
| **collaborator** | ❌ | ✅ | ❌ | ❌ |
| **advisor** | ❌ | 只读 | ❌ | ❌ |

#### 3. Agent ↔ Human 协作

```
┌─────────────┐         ┌─────────────┐
│    Agent    │◀───────▶│    Human    │
└─────────────┘         └─────────────┘
      │                        │
      │ agent 修改文档          │ 人类编辑
      ▼                        ▼
┌─────────────────────────────────────┐
│         Shared Workspace             │
│   (LaTeX / Jupyter / Notes / PDF)   │
└─────────────────────────────────────┘
```

### 不支持的功能

#### 1. 实时协作缺失

| 功能 | 缺失原因 |
|------|----------|
| **光标共享** | 无 CRDT/OT 协同算法 |
| **在线状态** | 无 WebSocket 广播用户状态 |
| **内联评论** | 仅 paper 级 Comment model |
| **变更追踪** | 无 diff/patch 机制 |
| **多用户编辑** | 每次仅一人 + agent 可写 |

#### 2. 版本控制不足

| 功能 | 当前状态 | 说明 |
|------|----------|------|
| **Workspace Snapshots** | ⚠️ 存在 | 用于状态回放，非文档版本 |
| **文档版本历史** | ❌ 无 | 无 `.tex` 文件版本记录 |
| **比较功能** | ❌ 无 | 无法 diff 两个版本 |

## 协作基础设施分析

### 现有数据模型

```prisma
// Workspace 参与者
model WorkspaceMember {
  id          String   @id @default(cuid())
  workspaceId String
  userId      String
  role        Role     // owner, member, agent, collaborator, advisor
  joinedAt    DateTime @default(now())

  @@unique([workspaceId, userId])
}

// 消息
model Message {
  id             String   @id @default(cuid())
  conversationId String
  senderId       String
  content        String
  type           MessageType // text, system, agent
  createdAt      DateTime @default(now())
}

// 评论 (仅 paper 级)
model Comment {
  id        String   @id @default(cuid())
  paperId   String
  authorId  String
  content   String
  pageNum   Int?     // 可选：页码
  position  Json?     // 可选：位置坐标
  createdAt DateTime @default(now())
}
```

### 缺失的协同组件

```
┌──────────────────────────────────────────────────────────────┐
│                   缺失的协作组件                                │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ❌ Yjs / Automerge    — CRDT 协同引擎                       │
│  ❌ WebSocket 广播     — 用户在线状态                         │
│  ❌ 评论锚点系统       — 文本范围评论                        │
│  ❌ 变更日志          — 操作历史记录                         │
│  ❌ Diff 算法         — 版本比较                             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## 架构原因分析

### 为什么 Prismer 缺乏实时协作

**设计优先级**:

```
1. AI 优先       ████████████████████ 60%
2. 个人效率       ████████████         30%
3. 团队协作       ████                 10%
```

**技术原因**:

1. **Directive 协议是单向的**
   - Agent → Frontend 推送
   - 但不支持 User ↔ User 同步

2. **状态存储是中央式的**
   - MySQL 持久化
   - 无 operational transform

3. **SyncMatrixEngine 不支持多人**
   - 11 条规则都是单用户设计
   - 无冲突解决机制

## 对比: Notion / Google Docs 协作架构

```
┌─────────────────────────────────────────────────────────────┐
│                  实时协作架构示例                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Client A          Client B          Client C              │
│      │                 │                 │                  │
│      └────────┬────────┴────────┬────────┘                  │
│               ▼                 ▼                           │
│        ┌────────────┐   ┌────────────┐                      │
│        │  Yjs Doc   │   │  Presence  │  ← 用户在线状态      │
│        │ (CRDT)     │   │  Service   │                      │
│        └─────┬──────┘   └────────────┘                      │
│              │                                                │
│              ▼                                                │
│        WebSocket Hub  ←──────────────▶ 广播所有变更            │
│              │                                                │
│              ▼                                                │
│        Database (最终一致性)                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Workaround 方案

### 当前可用协作方式

| 方式 | 实现 | 效果 |
|------|------|------|
| **IM 消息** | 内置消息系统 | 基本沟通 |
| **分享 Workspace** | 邀请成员 | 共享工作区 |
| **Agent 中转** | Agent 作为信息桥梁 | 间接协作 |
| **手动导出/导入** | PDF/文件交换 | 低效同步 |

### Agent 作为协作桥梁

```
User A                    Agent                      User B
   │                        │                          │
   │── "帮我总结 B 的笔记" ─▶│                          │
   │                        │── 请求 User B 的笔记 ────▶│
   │                        │◀── B 的笔记内容 ──────────│
   │◀── 总结结果 ───────────│                          │
```

## 未来增强建议

### P0 (必须)

1. **实现用户在线状态**
   - WebSocket presence
   - 心跳检测

2. **添加评论功能**
   - 文本范围评论
   - @mention 通知

### P1 (重要)

3. **版本历史**
   - 文档快照
   - 回滚功能

4. **变更通知**
   - Agent 修改通知
   - 邮件/站内通知

### P2 (优化)

5. **光标共享**
   - Yjs 集成
   - 冲突解决

6. **实时编辑**
   - Google Docs 风格
   - 多人同时编辑

## 数据隐私与安全

### 当前权限模型

```prisma
model Workspace {
  visibility  WorkspaceVisibility // private, internal, public
}

model WorkspaceMember {
  role        Role
  permissions Permission[]  // READ, WRITE, ADMIN, EXECUTE_AGENT
}
```

### 访问控制流程

```
┌─────────────────────────────────────────────────────────────┐
│                    权限检查流程                               │
└─────────────────────────────────────────────────────────────┘

1. 用户发起请求
         │
         ▼
2. Middleware 提取 token
         │
         ▼
3. 验证 token → 获取 userId
         │
         ▼
4. 查询 WorkspaceMember
   WHERE workspaceId = ? AND userId = ?
         │
         ▼
5. 检查 role.permissions
         │
         ├──▶ 有权限 → 继续处理
         │
         └──▶ 无权限 → 返回 403
```

## 结论

| 评估 | 说明 |
|------|------|
| **当前定位** | AI 增强的个人工作区，非团队协作平台 |
| **协作能力** | 基础设施存在 (participants, IM)，但非实时文档同步 |
| **核心差异** | Overleaf 团队协作优先 vs. Prismer AI 优先 |
| **适用场景** | 单用户 + AI 协作 vs. 多用户实时协同 |
