# 代码库地图

> 列出项目中所有源码文件及其职责，方便 AI 快速定位。

## 模块调用关系

```
main.py
  ├── routers/auth.py       → services/auth.py, services/mail.py, services/upload.py
  ├── routers/activities.py → services/member.py, services/log.py
  ├── routers/members.py    → services/log.py, services/user_attribute.py
  ├── routers/groups.py     → services/log.py
  ├── routers/logs.py
  └── middleware/auth.py    → services/auth.py

routers → schemas → models → database.py
```

## 后端（backend/）

### 应用入口

| 文件 | 职责 |
|------|------|
| `app/main.py` | FastAPI 入口：CORS 配置、静态文件挂载、子路由注册 |
| `app/config.py` | 读取 `.env`，导出数据库/SMTP/Session/上传目录/密码要求等全局配置 |
| `app/database.py` | SQLAlchemy 引擎/Session 工厂、`Base` 基类、`get_db` 依赖注入 |

### ORM 模型（app/models/）

| 文件 | 职责 |
|------|------|
| `__init__.py` | 汇总导出所有模型 |
| `user.py` | `User` 表 |
| `session.py` | `Session` 表：服务端 session 持久化 |
| `password_reset.py` | `PasswordReset` 表：密码重置令牌 |
| `activity.py` | `Activity` 表：活动（id, slug, user_id FK, title, description, group_strategy, group_param, constraints JSON） |
| `activity_member.py` | `ActivityMember` 表：活动成员关系，联合唯一约束 |
| `group.py` | `Group` 表：分组，关联 GroupMember |
| `group_member.py` | `GroupMember` 表：分组成员关系，联合唯一约束 |
| `member_attribute.py` | `MemberAttribute` 表：成员属性值，联合唯一约束，ON DELETE CASCADE |
| `activity_log.py` | `ActivityLog` 表：活动操作日志（detail 为 TEXT 存储 JSON 字符串） |
| `user_attribute.py` | `UserAttribute` 表：用户个人属性值，联合唯一约束 |

### Pydantic Schema（app/schemas/）

| 文件 | 职责 |
|------|------|
| `__init__.py` | 汇总导出所有 schema |
| `auth.py` | 认证相关：注册、登录、改密、重置密码、更新资料、用户响应、个人属性 |
| `activity.py` | 活动相关：约束规则、活动创建/更新/响应、成员条目、分组响应、日志响应 |

### API 路由（app/routers/）

| 文件 | 职责 |
|------|------|
| `__init__.py` | 汇总导出所有路由 |
| `auth.py` | `/api/auth/*` — 注册/登录/登出/me/改密/忘记密码/重置密码/更新资料/头像/注销账号/个人属性 |
| `activities.py` | `/api/activities` — POST 创建、GET 列表、GET `/:slug` 详情、PUT `/:slug` 编辑、DELETE `/:slug` 删除 |
| `members.py` | `/api/activities/:slug` — POST join/leave、PUT attributes、DELETE members/:user_id |
| `groups.py` | `/api/activities/:slug` — POST groups（含重新分组）、DELETE groups（解除分组） |
| `logs.py` | `/api/activities/:slug` — GET logs（仅创建者，按时间倒序） |

### 业务服务（app/services/）

| 文件 | 职责 |
|------|------|
| `__init__.py` | 汇总导出业务函数 |
| `auth.py` | 密码哈希/校验、注册/登录、Session 管理、密码重置、用户删除 |
| `mail.py` | SMTP 邮件发送（`send_reset_email`）、随机令牌生成（`generate_token`） |
| `upload.py` | 文件魔术头校验（`validate_magic_bytes`） |
| `member.py` | `get_attribute_warnings` — 检查成员属性值合规性 |
| `log.py` | `add_activity_log` — 写入活动操作日志 |
| `user_attribute.py` | `sync_user_attributes` — 同步用户个人属性值 |

### 中间件（app/middleware/）

| 文件 | 职责 |
|------|------|
| `__init__.py` | 导出 `get_current_user`、`RateLimiter` |
| `auth.py` | `get_current_user` 依赖注入：从 Cookie session_id 校验并返回当前 User |
| `rate_limit.py` | `RateLimiter` 类：基于 IP + 路径的滑动窗口频率限制，每 100 次请求清理过期键 |

### 数据库迁移（alembic/）

| 文件 | 职责 |
|------|------|
| `env.py` | Alembic 引擎配置，关联 Base.metadata |
| `versions/802b0df17e93_init.py` | 初始迁移：users、sessions、password_resets |
| `versions/4ebf2b01b301_add_activities_table.py` | 新增 activities 表 |
| `versions/4373c7646a4b_add_activity_members_table.py` | 新增 activity_members 表 |
| `versions/d9158a7c8e2f_add_slug_to_activities.py` | activities 表新增 slug 列 |
| `versions/5a1b2c3d4e5f_add_groups_and_group_members.py` | 新增 groups 和 group_members 表 |
| `versions/6b2c3d4e5f6a_add_group_strategy_to_activities.py` | activities 表新增 group_strategy、group_param、remainder_handling 字段 |
| `versions/7c3d4e5f6a7b_remove_remainder_handling.py` | activities 表删除 remainder_handling 字段 |
| `versions/8d4e5f6a7b8c_add_constraints_to_activities.py` | activities 表新增 constraints JSON 字段 |
| `versions/9e5f6a7b8c9d_add_member_attributes_table.py` | 新增 member_attributes 表 |
| `versions/a0f5b6c7d8e9_add_activity_logs_table.py` | 新增 activity_logs 表 |
| `versions/b1c6d7e8f9a0_add_user_attributes_table.py` | 新增 user_attributes 表（⬅ 当前 HEAD） |

---

## 前端（frontend/src/）

### 入口与路由

| 文件 | 职责 |
|------|------|
| `main.js` | Vue 3 入口：创建 Pinia、Router，挂载 `#app` |
| `App.vue` | 根组件：顶部导航栏 + `<router-view>` + 全局样式 |
| `style.css` | CSS reset 与字体渲染优化 |
| `router/index.js` | 路由表 + `beforeEach` 鉴权守卫 + 登录重定向 + 404 兜底路由 |

### API 调用层（api/）

| 文件 | 职责 |
|------|------|
| `index.js` | Axios 实例：baseURL、withCredentials、响应拦截器（422 数组展平、状态码兜底错误消息） |
| `auth.js` | 认证 API：注册/登录/登出/me/改密/忘记密码/重置密码/更新资料/头像/注销/个人属性 |
| `activities.js` | 活动 API：活动 CRUD、加入/退出/踢出、分组/解除、日志、更新属性 |

### 状态管理（stores/）

| 文件 | 职责 |
|------|------|
| `auth.js` | Pinia store：user 状态、isLoggedIn、fetchUser/login/logout |

### 工具函数（utils/）

| 文件 | 职责 |
|------|------|
| `date.js` | `formatDate` / `formatDateTime` 统一日期/时间格式化 |
| `groupRule.js` | 分组策略选项列表与标签映射 |
| `constraintPresets.js` | 组内多样性限定预设属性名列表 |

### 可复用组合式函数（composables/）

| 文件 | 职责 |
|------|------|
| `useAsyncState.js` | 封装 loading/error/data 异步状态管理 |

### 通用组件（components/）

| 文件 | 职责 |
|------|------|
| `ConstraintEditor.vue` | 组内多样性限定规则编辑器 |
| `AttributeSelector.vue` | 属性选择弹框：加入/编辑属性值 |
| `ConfirmModal.vue` | 确认对话框组件 |
| `MemberItem.vue` | 成员条目组件：头像、昵称、属性标签、高亮、警告、编辑入口、踢出按钮 |

### 页面组件（views/）

| 文件 | 职责 |
|------|------|
| `HomeView.vue` | 首页：我创建的活动列表 + 我加入的活动列表 |
| `CreateActivityView.vue` | 创建活动页 |
| `ActivityDetailView.vue` | 活动详情页：操作按钮栏、分组规则展示、成员列表（含分组/落单视图）、属性选择、确认对话框 |
| `ActivityEditView.vue` | 编辑活动页 |
| `LoginView.vue` | 登录页 |
| `RegisterView.vue` | 注册页 |
| `ForgotPasswordView.vue` | 忘记密码页 |
| `ResetPasswordView.vue` | 重置密码页 |
| `ChangePasswordView.vue` | 修改密码页 |
| `SettingsView.vue` | 个人设置页 |
| `NotFoundView.vue` | 404 页面 |
| `ActivityLogsView.vue` | 操作日志页 |
