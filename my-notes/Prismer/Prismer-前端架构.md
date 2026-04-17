---
title: Prismer 前端架构
description: Next.js 16 + React 19 + Zustand 5 技术栈深度分析
---

# Prismer 前端架构

## 技术栈全景

| 层级 | 技术 | 版本/规格 | 说明 |
|------|------|-----------|------|
| **Framework** | Next.js | 16 | App Router |
| **UI Library** | React | 19 | 全新特性 |
| **Language** | TypeScript | strict mode | 类型安全 |
| **Styling** | Tailwind CSS | 4 | OKLCH 色彩空间 |
| **Animation** | tw-animate-css | — | Tailwind 动画 |
| **UI Components** | shadcn/ui | — | Radix UI + CVA |
| **State** | Zustand | 5 | 10 个 Store |

## 项目结构

```
web/
├── src/
│   ├── app/
│   │   └── workspace/
│   │       ├── stores/          # Zustand stores
│   │       │   ├── layoutStore.ts
│   │       │   ├── chatStore.ts
│   │       │   ├── taskStore.ts
│   │       │   ├── timelineStore.ts
│   │       │   ├── componentStore.ts
│   │       │   ├── agentInstanceStore.ts
│   │       │   └── syncActions.ts
│   │       └── page.tsx
│   ├── lib/
│   │   ├── sync/                # 同步引擎
│   │   │   ├── index.ts
│   │   │   ├── SyncMatrixEngine.ts
│   │   │   ├── defaultMatrix.ts
│   │   │   └── componentStateConfig.ts
│   │   ├── services/            # 服务层
│   │   │   ├── workspace.service.ts
│   │   │   ├── im.service.ts
│   │   │   └── workspace-file-sync.service.ts
│   │   └── utils/
│   └── components/
│       ├── ui/                 # shadcn/ui
│       └── workspace/           # 自定义工作区组件
├── prisma/
│   └── schema.prisma            # 37 models
└── package.json
```

## Zustand 5 Store 详解

### 10 个 Store 职责矩阵

| Store | 文件 | State 核心字段 | Actions 数量 | 职责描述 |
|-------|------|---------------|-------------|----------|
| **layoutStore** | `layoutStore.ts` | panelSizes, collapsedSections | ~15 | 工作区面板布局 |
| **chatStore** | `chatStore.ts` | messages, participants, toolCalls | ~20 | 对话与消息 |
| **taskStore** | `taskStore.ts` | tasks, taskStateMachine | ~12 | 任务状态机 |
| **timelineStore** | `timelineStore.ts` | snapshots, events, cursor | ~8 | 时间线回放 |
| **componentStore** | `componentStore.ts` | activeComponents, componentStates | ~10 | 组件状态 |
| **agentInstanceStore** | `agentInstanceStore.ts` | instances, healthStatus | ~8 | Agent 生命周期 |
| **syncActions** | `syncActions.ts` | — | 80+ | 跨 Store 协调 |

### Store 间依赖关系

```
┌─────────────────────────────────────────────────────┐
│                    syncActions                        │
│              (80+ 跨 Store 协调动作)                  │
└─────────────────┬───────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┬─────────────┐
    │             │             │             │
    ▼             ▼             ▼             ▼
┌────────┐  ┌────────┐  ┌────────────┐  ┌────────────────┐
│ layout │  │  chat  │  │ component  │  │ agentInstance  │
│ Store  │  │ Store  │  │   Store    │  │    Store       │
└────────┘  └────────┘  └────────────┘  └────────────────┘
    │             │             │             │
    └─────────────┴─────────────┴─────────────┘
                         │
                    ┌────▼────┐
                    │ timeline │
                    │  Store  │
                    └─────────┘
```

### Workspace 隔离存储模式

**Key 格式**:
```
{userId}:{baseKey}:ws-{workspaceId}
```

**示例**:
```
user-abc123:chatStore:ws-xyz789
user-abc123:layoutStore:ws-xyz789
user-abc123:componentStore:ws-xyz789
```

**隔离实现**:
```typescript
// 每个 store 的 key 生成逻辑
const getStoreKey = (userId: string, baseKey: string, workspaceId: string) =>
  `${userId}:${baseKey}:ws-${workspaceId}`;
```

## Sync Layer 深度解析

### SyncMatrixEngine

**位置**: `web/src/lib/sync/SyncMatrixEngine.ts`

**核心职责**:
1. 规则驱动同步
2. 权限检查
3. 端点路由
4. 节流控制

**架构**:
```typescript
interface SyncRule {
  field: string;           // 同步字段
  direction: 'push' | 'pull' | 'bidirectional';
  throttle: number;       // 节流 ms
  permission: 'owner' | 'member' | 'agent';
}
```

### 11 条同步规则

| # | 规则名 | 同步字段 | 方向 | 节流 |
|---|--------|----------|------|------|
| 1 | messages | messages[] | push | 100ms |
| 2 | tasks | tasks[] | bidirectional | 200ms |
| 3 | timeline | snapshots[] | push | 500ms |
| 4 | componentStates | componentStates{} | bidirectional | 100ms |
| 5 | layout | panelLayout | pull | 300ms |
| 6 | chatReadState | readState{} | push | 150ms |
| 7 | toolCalls | toolCalls[] | push | 100ms |
| 8 | agentHealth | healthStatus | pull | 1000ms |
| 9 | fileSync | fileStates{} | bidirectional | 500ms |
| 10 | latexState | latexState{} | bidirectional | 200ms |
| 11 | jupyterState | jupyterState{} | bidirectional | 200ms |

### componentStateConfig.ts

**字段级同步配置**:

```typescript
interface ComponentSyncConfig {
  componentType: 'latex' | 'jupyter' | 'pdf' | 'notes';
  fields: {
    fieldName: string;
    syncable: boolean;
    priority: 'high' | 'medium' | 'low';
  }[];
}
```

### useAgentConnection Hook

**WebSocket 连接管理**:

```typescript
interface ConnectionConfig {
  url: string;
  reconnect: {
    enabled: boolean;
    maxAttempts: number;
    backoffMultiplier: number;
    initialDelay: number;  // ms
  };
  heartbeat: {
    interval: number;       // ms
    timeout: number;        // ms
  };
}
```

**指数退避策略**:
```
attempt 1: 1000ms
attempt 2: 2000ms
attempt 3: 4000ms
attempt 4: 8000ms
...
max: 30000ms
```

## Directive 协议详解

### 通信流程

```
┌─────────────┐     POST /api/agents/${agentId}/directive     ┌─────────────┐
│   Agent    │ ──────────────────────────────────────────────▶│   Bridge    │
│   Tools    │                                              │    API      │
└─────────────┘                                              └──────┬──────┘
                                                                    │
                                                                    ▼
                                                          ┌─────────────────┐
                                                          │  EventEmitter   │
                                                          │     Queue       │
                                                          └──────┬────────┘
                                                                 │
                                                                 ▼
                                                          ┌─────────────────┐
                                                          │   SSE Stream    │
                                                          └──────┬────────┘
                                                                 │
                                                                 ▼
                                                          ┌─────────────────┐
                                                          │ useDirective    │
                                                          │   Stream        │
                                                          └──────┬────────┘
                                                                 │
                                                                 ▼
                                                          ┌─────────────────┐
                                                          │ executeDirective│
                                                          │  → Store        │
                                                          │    Mutation     │
                                                          └──────┬────────┘
                                                                 │
                                                                 ▼
                                                          ┌─────────────────┐
                                                          │  Component      │
                                                          │   Re-render     │
                                                          └─────────────────┘
```

### Directive 类型详细定义

| Directive | payload 结构 | 触发组件 |
|-----------|--------------|----------|
| `SWITCH_COMPONENT` | `{ component: 'latex' \| 'jupyter' \| 'pdf' \| 'notes' }` | WorkspaceView |
| `LATEX_COMPILE_COMPLETE` | `{ projectId, pdfBase64, errors[] }` | PDFPreview |
| `LATEX_COMPILE_ERROR` | `{ projectId, errors[], lineNumbers[] }` | LaTeXEditor |
| `JUPYTER_CELL_RESULT` | `{ cellId, output, executionTime }` | JupyterCell |
| `JUPYTER_KERNEL_BUSY` | `{ busy: boolean }` | JupyterStatus |
| `UPDATE_NOTES` | `{ content, cursorPosition }` | NotesEditor |
| `UPDATE_GALLERY` | `{ chartType, dataUrl, config }` | DataGallery |
| `PAPER_LOADED` | `{ paperId, metadata }` | PDFViewer |
| `AGENT_TYPING` | `{ agentId, typing: boolean }` | ChatBubble |

### Directive 执行示例

```typescript
// SWITCH_COMPONENT directive 执行
const executeDirective = (directive: Directive) => {
  switch (directive.type) {
    case 'SWITCH_COMPONENT':
      componentStore.setActive(directive.payload.component);
      break;
    case 'LATEX_COMPILE_COMPLETE':
      latexStore.setPdf(directive.payload.pdfBase64);
      break;
    case 'JUPYTER_CELL_RESULT':
      jupyterStore.setCellOutput(
        directive.payload.cellId,
        directive.payload.output
      );
      break;
    // ...
  }
};
```

## UI 组件生态

### shadcn/ui 配置

**CVA (Class Variance Authority)**:
```typescript
// 按钮变体示例
const buttonVariants = cva('inline-flex items-center justify-center', {
  variants: {
    variant: {
      default: 'bg-primary text-primary-foreground',
      outline: 'border border-input',
      ghost: 'hover:bg-accent',
    },
    size: {
      default: 'h-10 px-4 py-2',
      sm: 'h-9 px-3',
      lg: 'h-11 px-8',
    },
  },
});
```

### Radix UI 原始组件使用

| 组件 | 用途 |
|------|------|
| @radix-ui/react-dialog | 模态对话框 |
| @radix-ui/react-dropdown-menu | 下拉菜单 |
| @radix-ui/react-tabs | 标签页 |
| @radix-ui/react-tooltip | 工具提示 |
| @radix-ui/react-scroll-area | 滚动区域 |

## 性能优化策略

| 策略 | 实现 |
|------|------|
| **Zustand 切片** | 每个 store 独立，延迟加载 |
| **Sync 节流** | defaultMatrix.ts 中定义各字段节流 |
| **WebSocket 心跳** | useAgentConnection 定期 ping |
| **SSE 流控** | Server-Sent Events 背压处理 |
| **组件懒加载** | Next.js dynamic import |

## 错误处理机制

```typescript
// useAgentConnection 错误处理
const errorHandler = {
  onConnectionError: (error: Error, attempt: number) => {
    if (attempt < maxAttempts) {
      scheduleReconnect(attempt);
    } else {
      agentInstanceStore.setStatus('disconnected');
      // 通知用户重连选项
    }
  },
  onMessageError: (message: any) => {
    console.error('Invalid message format:', message);
  },
};
```
