---
title: Prismer 后端架构
description: Prisma + SQLite/MySQL + WebSocket 协议深度分析
---

# Prismer 后端架构

## 技术栈概览

| 层级 | 技术 | 说明 |
|------|------|------|
| **ORM** | Prisma | 数据库抽象层 |
| **数据库** | SQLite (dev) / MySQL (prod) | 数据持久化 |
| **API** | Next.js API Routes | REST + WebSocket |
| **实时通信** | Server-Sent Events | 服务端推送 |
| **WebSocket** | ws 库 | 双向实时通信 |

## 数据库架构

### Prisma Schema 规模

- **37 个数据模型**
- **7 个域 (domains)**

### 核心数据模型

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ WorkspaceSession│ ←→  │  AgentInstance  │ ←→  │    Container    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
   会话管理                Agent 生命周期            运行环境
```

### 37 个模型分类 (7 域)

| 域 | 模型数 | 示例模型 |
|---|--------|----------|
| User | ~5 | User, UserPreference, UserSession |
| Workspace | ~8 | Workspace, WorkspaceSession, WorkspaceMember |
| Agent | ~6 | AgentInstance, AgentTemplate, AgentHealth |
| Message | ~5 | Message, Conversation, DirectMessage |
| File | ~4 | File, FileVersion, FileSyncState |
| Component | ~4 | LaTeXProject, JupyterNotebook, PDFDocument |
| Audit | ~5 | AuditLog, SyncState, TimelineSnapshot |

### 关键模型关系

```prisma
model Workspace {
  id          String   @id @default(cuid())
  name        String
  ownerId     String
  members     WorkspaceMember[]
  sessions    WorkspaceSession[]
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}

model WorkspaceSession {
  id            String   @id @default(cuid())
  workspaceId   String
  workspace     Workspace @relation(fields: [workspaceId], references: [id])
  agentInstance AgentInstance?
  containerId   String?
  status        SessionStatus
  createdAt     DateTime @default(now())
}

model AgentInstance {
  id          String   @id @default(cuid())
  sessionId   String   @unique
  session     WorkspaceSession @relation(fields: [sessionId], references: [id])
  templateId  String
  provider    String   // "kimi" | "claude"
  model       String   // "kimi-k2.5" | "sonnet-4"
  status      AgentStatus
  health      AgentHealth?
  createdAt   DateTime @default(now())
}
```

### SQLite vs MySQL

| 场景 | 数据库 | 原因 |
|------|--------|------|
| 开发 | SQLite | 零配置，快速启动 |
| 生产 | MySQL | 并发支持，数据量 |

## API 路由架构

### 路由结构

```
/api/
├── v2/
│   └── im/
│       └── bridge/
│           └── [workspaceId]/    # 中央枢纽
│               └── route.ts
├── workspace/
│   └── [id]/                     # 工作区 CRUD
│       └── route.ts
├── agents/
│   └── [id]/
│       ├── start/               # Agent 启动
│       │   └── route.ts
│       └── directive/           # Directive 转发
│           └── route.ts
├── files/
│   ├── upload/
│   ├── download/
│   └── sync/
└── latex/
    ├── compile/
    └── templates/
```

### 中央枢纽: Bridge API

**路由**: `/api/v2/im/bridge/[workspaceId]`

**职责**: 接收用户消息 → 转发到 Container Gateway → 返回 Agent 响应 + Directives

**请求格式**:
```typescript
interface BridgeRequest {
  type: 'message' | 'directive' | 'sync';
  payload: {
    content: string;
    attachments?: Attachment[];
    context?: {
      component?: string;
      toolCallId?: string;
    };
  };
}
```

**响应格式**:
```typescript
interface BridgeResponse {
  type: 'response' | 'stream' | 'directive';
  data: {
    agentId: string;
    content: string;
    directives?: Directive[];
    toolCalls?: ToolCall[];
  };
}
```

### Workspace CRUD API

**路由**: `/api/workspace/[id]`

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/workspace/[id]` | 获取工作区信息 |
| PUT | `/api/workspace/[id]` | 更新工作区 |
| DELETE | `/api/workspace/[id]` | 级联删除工作区 + Agent + Container |

**级联删除**:
```typescript
// DELETE /api/workspace/[id]
// 触发:
1. WorkspaceSession.delete(sessionId)
2. AgentInstance.stop(agentId)
3. Container.terminate(containerId)
4. FileSyncState.cleanup(workspaceId)
5. TimelineSnapshot.archive(workspaceId)
```

### Agent Start API

**路由**: `/api/agents/[id]/start`

**响应**: 返回静态配置的存根
```typescript
interface AgentStartResponse {
  agentId: string;
  template: AgentTemplate;
  config: {
    provider: 'kimi' | 'claude';
    model: string;
    gatewayUrl: string;
    gatewayPort: number;
  };
}
```

## 服务层架构

### 服务文件结构

```
web/src/lib/services/
├── workspace.service.ts
├── im.service.ts
├── workspace-file-sync.service.ts
├── container.service.ts
└── agent.service.ts
```

### Workspace Service

**职责**: Workspace CRUD + Agent 模板管理

```typescript
interface WorkspaceService {
  // CRUD
  create(data: CreateWorkspaceDTO): Promise<Workspace>;
  findById(id: string): Promise<Workspace | null>;
  update(id: string, data: UpdateWorkspaceDTO): Promise<Workspace>;
  delete(id: string): Promise<void>;

  // Agent 模板
  getAgentTemplates(): AgentTemplate[];
  createSession(workspaceId: string, templateId: string): Promise<WorkspaceSession>;
}
```

### IM Service

**职责**: 即时通讯相关服务

```typescript
interface IMService {
  // 用户
  getOrCreateUser(userId: string): Promise<IMUser>;

  // 对话
  getConversations(workspaceId: string): Promise<Conversation[]>;
  createConversation(data: CreateConversationDTO): Promise<Conversation>;

  // 消息
  sendMessage(conversationId: string, content: string): Promise<Message>;
  getMessages(conversationId: string, limit: number): Promise<Message[]>;
}
```

### Workspace File Sync Service

**职责**: Container → S3 → MySQL → Collection 同步管道

```
┌───────────┐     ┌─────────┐     ┌──────────┐     ┌───────────┐
│ Container │ ──▶ │   S3    │ ──▶ │  MySQL   │ ──▶ │ Collection │
│  (local)  │     │ (files) │     │ (metadata)│     │  (index)   │
└───────────┘     └─────────┘     └──────────┘     └───────────┘
```

```typescript
interface WorkspaceFileSyncService {
  // 文件同步
  uploadFromContainer(containerId: string, path: string): Promise<S3Url>;
  downloadToContainer(containerId: string, s3Url: string): Promise<void>;

  // 元数据
  updateFileMetadata(workspaceId: string, fileId: string, metadata: FileMetadata): Promise<void>;

  // 索引
  reindexWorkspace(workspaceId: string): Promise<void>;
}
```

## WebSocket 协议

### 连接握手流程

```
Client                          Server
  │                                │
  │ ──── connect.challenge ────▶ │  1. Server 发送 challenge
  │                                │
  │ ◀─── connect.challenge ────── │  2. Client 接收
  │                                │
  │ ──── connect ─────────────────▶│  3. Client 发送 token + signed nonce
  │     { token, signedNonce }     │
  │                                │
  │ ◀─── hello-ok ─────────────── │  4. Server 验证并返回 session token
  │     { sessionToken }          │
  │                                │
  │ ◀═══ connection established ═══│
```

### 消息类型

| 消息类型 | 方向 | 用途 |
|----------|------|------|
| `connect.challenge` | S→C | 连接挑战 |
| `connect` | C→S | 连接请求 |
| `hello-ok` | S→C | 连接确认 |
| `chat.send` | C→S | 发送消息 |
| `chat.message` | S→C | 接收消息 |
| `tool.call` | S→C | 工具调用 |
| `tool.result` | C→S | 工具结果 |
| `directive.send` | S→C | 发送指令 |
| `ping` | C→S | 心跳 |
| `pong` | S→C | 心跳响应 |
| `disconnect` | C→S/S→C | 断开连接 |

### 消息格式

```typescript
// WebSocket 消息结构
interface WSMessage {
  type: string;
  id: string;          // 消息 ID，用于追踪
  timestamp: number;    // Unix timestamp
  payload: any;
}

// 示例: chat.send
interface ChatSendMessage {
  type: 'chat.send';
  id: 'msg-001';
  timestamp: 1713400000;
  payload: {
    conversationId: 'conv-123';
    content: '帮我编译这个 LaTeX 文档';
    attachments?: string[];
  };
}

// 示例: chat.message (streaming)
interface ChatMessage {
  type: 'chat.message';
  id: 'msg-001';
  timestamp: 1713400001;
  payload: {
    conversationId: 'conv-123';
    agentId: 'agent-456';
    content: '好的，我开始编译...';
    delta?: boolean;     // 是否为增量更新
    done?: boolean;      // 是否完成
  };
}
```

## SSE (Server-Sent Events)

### 用于 Directive 推送

```typescript
// /api/agents/[id]/directive/route.ts

export async function GET(request: Request) {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      // 订阅 Directive 队列
      const unsubscribe = directiveQueue.subscribe((directive) => {
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify(directive)}\n\n`)
        );
      });

      // 清理
      request.signal.addEventListener('abort', () => {
        unsubscribe();
        controller.close();
      });
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}
```

## 安全性

### 认证流程

```
1. 用户登录 → 获取 JWT token
2. WebSocket 连接时携带 token
3. Server 验证 token + signed nonce
4. 生成 session token 用于后续通信
```

### 权限模型

| 角色 | 权限 |
|------|------|
| owner | 全部权限 |
| member | 读写自己的工作区内容 |
| agent | 读写分配给它的 workspace |
| collaborator | 只读 |
| advisor | 只读 + 建议 |

## 性能考量

| 优化点 | 策略 |
|--------|------|
| **数据库连接** | Prisma Connection Pool |
| **WebSocket 扩展** | 水平扩展 Gateway 实例 |
| **消息队列** | Directive 内存队列 + 持久化 |
| **文件同步** | 增量同步 + 压缩传输 |
| **查询优化** | 索引 + 分页 |
