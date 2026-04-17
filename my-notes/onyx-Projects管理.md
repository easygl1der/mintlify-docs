---
title: Projects 管理机制
description: Onyx 中个人项目（UserProject）的数据库模型、API 接口和生命周期管理
---

# Onyx Projects 管理机制

> 分析时间：2026-04-17
> 数据来源：多 Agent 并行分析

## 一、数据库模型

### UserProject 表结构

**文件位置**：`backend/onyx/db/models.py:4466-4485`

```python
class UserProject(Base):
    __tablename__ = "user_project"

    id: int                     # 主键，自增
    user_id: UUID               # 所有者用户 ID（外键 → user.id）
    name: str                   # 项目名称
    description: Optional[str] # 项目描述
    created_at: datetime        # 创建时间
    instructions: str           # 项目特定指令（Agent 行为配置）
```

### 关联关系表

| 表名 | 说明 |
|------|------|
| `project__user_file` | 项目-用户文件多对多关系 |
| `ChatSession.project_id` | 聊天会话 → 项目（一对多） |

## 二、项目生命周期

### 1. 创建（Creation）
**API 端点**：`POST /user/projects/create`

**文件位置**：`backend/onyx/server/features/projects/api.py:112-124`

```python
@router.post("/create")
def create_project(
    name: str,
    description: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> UserProjectSnapshot:
    project = UserProject(
        name=name,
        user_id=user.id,
        description=description,
    )
    db_session.add(project)
    db_session.commit()
    return project
```

### 2. 文件关联（File Association）
- 文件通过 `upload_files_to_user_files_with_indexing()` 上传
- 创建 `UserFile` 记录并关联到项目
- 通过 `project__user_file` 中间表建立多对多关系

### 3. 聊天会话（Chat Sessions）
- 项目可以有多个关联的聊天会话
- `ChatSession.project_id` 外键指向项目
- 支持在项目间移动聊天会话

### 4. 更新（Update）
- 修改项目名称、描述
- 更新项目指令（影响 Agent 行为）

### 5. 删除（Deletion）
**API 端点**：`DELETE /user/projects/{project_id}`

**文件位置**：`api.py:415-440`

删除流程：
1. 解除聊天会话与项目的关联
2. 移除 `project__user_file` 关联
3. 删除 `UserProject` 记录

## 三、API 端点

**文件位置**：`backend/onyx/server/features/projects/api.py`

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/user/projects` | 列出用户所有项目 |
| POST | `/user/projects/create` | 创建新项目 |
| GET | `/user/projects/{project_id}` | 获取单个项目 |
| PATCH | `/user/projects/{project_id}` | 更新项目 |
| DELETE | `/user/projects/{project_id}` | 删除项目 |
| GET | `/user/projects/files/{project_id}` | 列出项目文件 |
| POST | `/user/projects/{project_id}/files/{file_id}` | 关联文件到项目 |
| DELETE | `/user/projects/{project_id}/files/{file_id}` | 解除文件关联 |
| GET/POST | `/{project_id}/instructions` | 获取/更新项目指令 |
| POST | `/{project_id}/move_chat_session` | 移动聊天会话 |
| DELETE | `/remove_chat_session` | 移除聊天会话 |

## 四、前端实现

### ProjectsContext
**文件位置**：`web/src/providers/ProjectsContext.tsx`

```typescript
interface ProjectsContextValue {
  projects: UserProject[];
  recentFiles: UserFile[];
  currentProjectDetails: UserProject | null;
  currentProjectId: number | null;

  // Operations
  createProject: (name: string, description?: string) => Promise<UserProject>;
  renameProject: (id: number, name: string) => Promise<void>;
  deleteProject: (id: number) => Promise<void>;
  uploadFiles: (projectId: number, files: File[]) => Promise<UserFile[]>;
  getFilesInProject: (projectId: number) => Promise<UserFile[]>;
}
```

### 状态管理特点
- **SWR** 数据获取和缓存
- **乐观更新**（Optimistic Updates）提升上传体验
- **轮询** 文件状态直到处理完成

### API 路由映射

| 前端调用 | 后端端点 |
|----------|----------|
| `GET /api/user/projects` | `/user/projects` |
| `POST /api/user/projects/create` | `/user/projects/create` |
| `PATCH /api/user/projects/${id}` | `/user/projects/${id}` |
| `DELETE /api/user/projects/${id}` | `/user/projects/${id}` |
| `POST /api/user/projects/file/upload` | `/user/projects/file/upload` |

## 五、文件上传流程

### 完整链路
```
前端选择文件
    ↓
POST /api/user/projects/file/upload
    ↓
API 接收 → 保存文件 → 创建 UserFile 记录
    ↓
Celery 任务 PROCESS_SINGLE_USER_FILE 入队
    ↓
Worker 处理：
  - LocalFileConnector 加载文件
  - 文本提取（pypdf/markitdown）
  - 分块（SentenceChunker）
  - 嵌入向量生成
  - 存入 Vespa
    ↓
更新 UserFile.status = COMPLETED
    ↓
前端轮询感知状态变化
```

### 关键文件
**文件位置**：`backend/onyx/server/features/projects/api.py:127`

```python
@router.post("/user/projects/file/upload")
def upload_user_files(...) -> list[UserFileSnapshot]:
    return upload_files_to_user_files_with_indexing(...)
```

## 六、Project Instructions 机制

### 用途
`instructions` 字段存储项目特定的 Agent 行为配置：

```python
# 示例指令
PROJECT_INSTRUCTIONS = """
你是一个专业的技术文档助手。
只回答与项目文档相关的问题。
使用项目中的文档作为主要参考。
"""
```

### 获取/更新
```python
@router.get("/{project_id}/instructions")
def get_project_instructions(project_id: int, ...):
    project = db.query(UserProject).filter_by(id=project_id).first()
    return {"instructions": project.instructions}

@router.post("/{project_id}/instructions")
def update_project_instructions(project_id: int, instructions: str, ...):
    project.instructions = instructions
    db.commit()
```

## 七、Projects vs Groups 区别

| 维度 | Projects | Groups |
|------|----------|--------|
| **作用域** | 个人私有 | 组织共享 |
| **数据模型** | `user_id` 所有者 | 多用户关联 |
| **核心功能** | 文件组织、聊天管理 | 访问控制、资源共享 |
| **API 路径** | `/user/projects/*` | `/manage/admin/user-group/*` |
| **权限模型** | 仅所有者可管理 | Curator + 成员 |
| **关联资源** | Files, Chat Sessions | Connectors, Agents, Documents |

## 八、数据流关系图

```
User (1)
  ↓ (1:N)
UserProject
  ↓ (N:N via project__user_file)
  ├── UserFile (1:N)
  │   └── 文档内容、状态、嵌入向量
  │
  ↓ (1:N)
  ChatSession
      └── Message (聊天消息)
```

## 九、使用场景

### 个人知识管理
```python
# 创建项目
project = create_project(
    name="机器学习笔记",
    description="学习 ML 的文档和笔记"
)

# 上传文件
upload_files_to_user_files_with_indexing(
    project_id=project.id,
    files=[pdf_file, pptx_file]
)

# 开始聊天
chat = create_chat_session(project_id=project.id)
```

### 项目协作（通过 Groups）
虽然 Projects 本身是私有的，但通过 Groups 机制可以：
1. 创建共享的 Connector（关联到 Group）
2. 用户在个人 Project 中访问 Group 资源
3. 实现一定程度的协作

## 十、关键实现细节

### 1. 文件索引状态追踪
```python
class UserFileStatus(str, Enum):
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
```

### 2. 乐观更新示例
```typescript
const uploadFiles = async (projectId: number, files: File[]) => {
  // 乐观添加
  mutate(
    `/api/user/projects/files/${projectId}`,
    (current) => [...current, ...newFiles],
    false
  );

  try {
    await fetch('/api/user/projects/file/upload', {...});
    mutate(`/api/user/projects/files/${projectId}`);
  } catch (error) {
    mutate(`/api/user/projects/files/${projectId}`); // 回滚
  }
};
```

### 3. 轮询文件状态
```typescript
// 使用 SWR 的 revalidateInterval
const { data: files } = useSWR(
  `/api/user/projects/files/${projectId}`,
  fetcher,
  { revalidateInterval: 2000 } // 每 2 秒轮询
);
```
