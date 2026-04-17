---
title: Onyx 整体架构分析
description: Onyx (原 Danswer) 开源 Gen-AI 企业搜索平台的整体架构分析
---

# Onyx 整体架构分析

> 分析时间：2026-04-17
> 数据来源：多 Agent 并行分析

## 一、项目概述

**Onyx**（前身为 Danswer）是一个开源的 Gen-AI 和企业搜索平台，连接公司文档、应用和人员。具备 MIT 社区版和商业企业版。

## 二、技术栈

### 后端架构
| 组件 | 技术 |
|------|------|
| 语言 | Python 3.11 |
| 框架 | FastAPI |
| 任务队列 | Celery（9 种 worker 类型） |
| 数据库 | PostgreSQL |
| 缓存 | Redis |
| 向量数据库 | Vespa |
| AI/ML | LiteLLM + LangChain |

### 前端架构
| 组件 | 技术 |
|------|------|
| 框架 | Next.js 16 + React 19 |
| 语言 | TypeScript 5.9 |
| 样式 | Tailwind CSS + Radix UI |
| 状态管理 | SWR + Zustand + React Context |
| 表单 | Formik + Yup |

### Celery Worker 类型
1. **Primary Worker** - 协调核心任务
2. **Docfetching Worker** - 从外部数据源获取文档
3. **Docprocessing Worker** - 文档索引管道处理
4. **Light Worker** - 轻量级快速操作
5. **Heavy Worker** - 资源密集型操作
6. **KG Processing Worker** - 知识图谱处理
7. **Monitoring Worker** - 系统健康监控
8. **User File Processing Worker** - 用户上传文件处理
9. **Beat Worker** - 定时任务调度

## 三、目录结构

```
backend/
├── onyx/                          # 社区版核心模块
│   ├── auth/                      # 认证授权
│   ├── chat/                      # 聊天功能
│   ├── connectors/                # 数据源连接器
│   ├── db/                        # 数据库模型
│   ├── document_index/            # Vespa 集成
│   ├── federated_connectors/      # 外部搜索连接器
│   ├── file_processing/           # 文件处理
│   ├── indexing/                  # 索引管道
│   ├── kg/                        # 知识图谱
│   ├── llm/                       # LLM 提供商集成
│   ├── server/                    # API 端点
│   └── tools/                     # 工具实现
├── ee/                           # 企业版功能
├── alembic/                      # 数据库迁移
└── tests/                        # 测试套件

web/
├── src/
│   ├── app/                       # Next.js App Router 页面
│   ├── components/                # 共享组件
│   ├── lib/                       # 工具函数
│   ├── providers/                  # React Context
│   └── hooks/                     # 自定义 Hooks
```

## 四、关键设计模式

### 1. 多租户支持
- 通过中间件自动识别租户 ID
- Celery Beat 使用 `DynamicTenantScheduler`
- 每个租户的任务隔离

### 2. 向量搜索架构
- **Vespa** 作为向量数据库
- 混合搜索：向量相似度 + 关键词搜索
- RRF（Reciprocal Rank Fusion）融合

### 3. LLM 抽象层
- **LiteLLM** 支持多提供商
- 可配置模型：聊天、嵌入、图像
- 流式响应支持

### 4. 错误处理
- 全局 FastAPI 异常处理器
- `OnyxError` 统一错误格式
- 结构化错误代码

## 五、数据流

```
用户上传文件
    ↓
API 接收 → 文件存储
    ↓
Celery 任务入队
    ↓
Docfetching Worker 获取文档
    ↓
Docprocessing Worker 处理
    ↓
文本提取 → 分块 → 嵌入 → Vespa 索引
    ↓
用户查询 → 混合检索 → LLM 生成 → 流式响应
```

## 六、API 架构

- **后端**：FastAPI + Pydantic 模型
- **前端代理**：`/api/[...path]` 捕获所有请求转发到后端
- **认证**：OAuth2 多提供商支持

## 七、关键文件映射

| 功能 | 后端路径 | 前端路径 |
|------|----------|----------|
| 文件上传 | `server/features/projects/api.py` | `components/chat/files/` |
| 搜索工具 | `tools/tool_implementations/search/` | `lib/search/` |
| LLM 循环 | `chat/llm_loop.py` | `components/chat/` |
| 用户组 | `ee/server/user_group/` | `admin/GroupsPage/` |

## 八、测试策略

1. **单元测试** - 模拟外部依赖
2. **外部依赖单元测试** - 真实外部服务，模拟 Onyx 本身
3. **集成测试** - 完整 Onyx 部署
4. **Playwright E2E** - 包含 Web Server 的端到端测试

## 九、项目定位

Onyx 定位为**企业级 AI 搜索平台**，核心价值：
- 🔍 多数据源统一搜索
- 💬 智能问答与 RAG
- 🔒 企业级安全与权限
- 📊 知识图谱增强
