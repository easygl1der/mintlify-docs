---
title: Groups 管理机制
description: Onyx 中用户组（UserGroup）的数据库模型、API 接口和管理机制深度分析
---

# Onyx Groups 管理机制

> 分析时间：2026-04-17
> 数据来源：多 Agent 并行分析

## 一、数据库模型

### UserGroup 表结构

**文件位置**：`backend/onyx/db/models.py:4147-4205`

```python
class UserGroup(Base):
    __tablename__ = "user_group"

    id: int                    # 主键
    name: str                  # 组名，唯一
    is_up_to_date: bool        # 是否已同步到 Vespa
    is_up_for_deletion: bool   # 是否标记删除
    is_default: bool           # 系统默认组（如 "Basic", "Admins"）
    time_last_modified_by_user: datetime  # 最后修改时间
```

### 关联关系表

| 表名 | 说明 |
|------|------|
| `user__user_group` | 用户-组多对多关系（含 `is_curator` 标志） |
| `user_group__connector_credential_pair` | 组-连接器凭证关联 |
| `persona__user_group` | 组-Agent/Persona 关联 |
| `document_set__user_group` | 组-文档集关联 |
| `credential__user_group` | 组-凭证关联 |
| `mcp_server__user_group` | 组-MCP 服务器关联 |

## 二、核心功能

### 1. Curator（策展人）机制
- `is_curator=True` 的用户可以管理组内资源
- Curator 可以添加/移除组成员
- Curator 可以管理组关联的连接器和文档

### 2. 资源访问控制
- Groups 控制对外部数据源（Connectors）的访问
- Groups 定义哪些 Agent/Persona 可用于特定用户
- Groups 关联文档集和凭证

### 3. 同步机制
- `is_up_to_date` 标记 Vespa 同步状态
- `is_up_for_deletion` 标记待清理的组

## 三、API 端点

**文件位置**：`backend/ee/onyx/server/user_group/api.py`

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/manage/admin/user-group` | 列出所有组（管理员） |
| GET | `/manage/user-groups/minimal` | 列出所有组（任何用户） |
| POST | `/manage/admin/user-group` | 创建组 |
| PATCH | `/manage/admin/user-group/{id}` | 更新组成员/资源 |
| PATCH | `/manage/admin/user-group/rename` | 重命名组 |
| DELETE | `/manage/admin/user-group/{id}` | 删除组 |
| POST | `/manage/admin/user-group/{id}/add-users` | 添加用户 |
| POST | `/manage/admin/user-group/{id}/set-curator` | 设置策展人 |
| GET/PUT | `/manage/admin/user-group/{id}/permissions` | 权限管理 |
| PATCH | `/manage/admin/user-group/{id}/agents` | 添加/移除 Agent |

## 四、前端实现

### 页面组件
**文件位置**：`web/src/refresh-pages/admin/GroupsPage/`

| 文件 | 说明 |
|------|------|
| `index.tsx` | 组列表主页 |
| `GroupsList.tsx` | 渲染过滤后的组卡片 |
| `GroupCard.tsx` | 单个组展示（可重命名/编辑） |
| `CreateGroupPage.tsx` | 新建组表单 |
| `EditGroupPage.tsx` | 完整编辑界面（标签页切换） |
| `svc.ts` | API 辅助函数 |

### TypeScript 接口
**文件位置**：`web/src/lib/types.ts:480-491`

```typescript
interface UserGroup {
  id: number;
  name: string;
  users: User[];
  curator_ids: string[];
  cc_pairs: CCPairDescriptor<any, any>[];
  document_sets: DocumentSetSummary[];
  personas: Persona[];
  is_up_to_date: boolean;
  is_up_for_deletion: boolean;
  is_default: boolean;
}
```

## 五、Groups vs Projects 区别

| 维度 | Groups | Projects |
|------|--------|----------|
| **所有者** | 系统/多用户共享 | 个人私有（user_id） |
| **用途** | 访问控制、资源共享 | 文件组织、聊天会话 |
| **权限模型** | Curator + 成员 | 仅所有者 |
| **关联资源** | Connectors, Agents, Documents | Files, Chat Sessions |
| **API 路径** | `/manage/admin/user-group` | `/user/projects` |

## 六、数据流关系图

```
User
├── user_group_relationships (N:N via user__user_group)
│   └── UserGroup
│       ├── users (N:N)
│       ├── cc_pairs (N:N) → ConnectorCredentialPair
│       ├── personas (N:N) → Persona (Agent)
│       ├── document_sets (N:N)
│       ├── credentials (N:N)
│       └── accessible_mcp_servers (N:N)
│
└── UserProject (1:N)
    └── UserProject
        ├── user_files (N:N)
        └── chat_sessions (1:N)
```

## 七、关键实现细节

### 1. 创建组
```python
@router.post("/manage/admin/user-group")
def create_user_group(
    name: str,
    user_ids: list[int] = [],
    curator_ids: list[str] = [],
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserGroup:
    # 验证权限
    # 创建 UserGroup 记录
    # 创建 user__user_group 关联
    # 调用 recompute_user_permissions__no_commit()
```

### 2. 权限重计算
修改组成员后必须调用：
```python
from onyx.access.access import recompute_user_permissions__no_commit
recompute_user_permissions__no_commit(db, user_id=user_id)
```

### 3. 默认组
系统创建不可删除的默认组：
- `Basic` - 基础用户组
- `Admins` - 管理员组

## 八、Enterprise Edition 扩展

Groups 管理功能主要在 **EE（Enterprise Edition）** 中实现：
- 文件位置：`backend/ee/onyx/server/user_group/`
- 社区版可能功能受限

## 九、安全考虑

1. **权限验证**：所有管理端点需要管理员权限
2. **数据隔离**：组资源访问通过权限系统控制
3. **审计日志**：组变更应记录操作日志
4. **删除保护**：默认组不可删除
