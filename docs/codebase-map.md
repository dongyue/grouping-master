# 代码库地图

> 列出项目中所有源码文件及其职责，方便 AI 快速定位。

## 后端（backend/）

### 应用入口

| 文件 | 职责 |
|------|------|
| `app/main.py` | FastAPI 入口：CORS 配置、静态文件挂载、路由注册 |
| `app/config.py` | 读取 `.env`，导出数据库/SMTP/Session/上传目录等全局配置 |
| `app/database.py` | SQLAlchemy 引擎/Session 工厂、`Base` 基类、`get_db` 依赖注入 |

### ORM 模型（app/models/）

| 文件 | 职责 |
|------|------|
| `__init__.py` | 汇总导出所有模型 |
| `user.py` | `User` 表：id, username, nickname, password_hash, email, avatar_path, 时间戳 |
| `session.py` | `Session` 表：服务端 session 持久化（id, user_id, data, expires_at） |
| `password_reset.py` | `PasswordReset` 表：密码重置令牌（token, expires_at, used） |
| `activity.py` | `Activity` 表：活动（id, slug, user_id FK, title, description, 时间戳），关联 User |
| `activity_member.py` | `ActivityMember` 表：活动成员关系（id, activity_id FK, user_id FK, 时间戳），联合唯一约束 |

### Pydantic Schema（app/schemas/）

| 文件 | 职责 |
|------|------|
| `__init__.py` | 汇总导出所有 schema |
| `auth.py` | 全部请求/响应校验：注册、登录、改密、重置密码、更新资料、头像、注销、活动 CRUD |

### API 路由（app/routers/）

| 文件 | 职责 |
|------|------|
| `__init__.py` | 汇总导出路由 |
| `auth.py` | `/api/auth/*` — 注册/登录/登出/me/改密/忘记密码/重置密码/更新资料/头像/注销账号 |
| `activities.py` | `/api/activities` — POST 创建、GET 列表、GET `/:slug` 详情、POST `/:slug` 加入/退出、PUT `/:slug` 编辑、DELETE `/:slug` 删除 |

### 业务服务（app/services/）

| 文件 | 职责 |
|------|------|
| `__init__.py` | 汇总导出业务函数 |
| `auth.py` | 密码哈希/校验、注册/登录、Session 创建/查询/删除、密码重置令牌生成 |
| `mail.py` | SMTP 邮件发送（`send_reset_email`）、随机令牌生成 |

### 中间件（app/middleware/）

| 文件 | 职责 |
|------|------|
| `auth.py` | `get_current_user` 依赖注入：从 Cookie session_id 校验并返回当前 User |

### 数据库迁移（alembic/）

| 文件 | 职责 |
|------|------|
| `env.py` | Alembic 引擎配置，关联 Base.metadata |
| `versions/802b0df17e93_init.py` | 初始迁移：users、sessions、password_resets 三表 |
| `versions/4ebf2b01b301_add_activities_table.py` | 新增 activities 表 |
| `versions/4373c7646a4b_add_activity_members_table.py` | 新增 activity_members 表 |
| `versions/d9158a7c8e2f_add_slug_to_activities.py` | activities 表新增 slug 列 |

---

## 前端（frontend/src/）

### 入口与路由

| 文件 | 职责 |
|------|------|
| `main.js` | Vue 3 入口：创建 Pinia、Router，挂载 `#app` |
| `App.vue` | 根组件：顶部导航栏 + `<router-view>` |
| `router/index.js` | 路由表 + `beforeEach` 鉴权守卫（requiresAuth/guest） |

### API 调用层（api/）

| 文件 | 职责 |
|------|------|
| `index.js` | Axios 实例：baseURL、withCredentials、响应/错误拦截器 |
| `auth.js` | 认证 API：注册/登录/登出/me/改密/忘记密码/重置密码/更新资料/头像/注销 |
| `activities.js` | 活动 API：createActivity、listActivities、getActivity、joinActivity、leaveActivity、updateActivity、deleteActivity |

### 状态管理（stores/）

| 文件 | 职责 |
|------|------|
| `auth.js` | Pinia store：user 状态、isLoggedIn、fetchUser/login/logout |

### 页面组件（views/）

| 文件 | 职责 |
|------|------|
| `HomeView.vue` | 首页：活动创建表单 + 我的活动列表（点击可跳转详情） |
| `ActivityDetailView.vue` | 活动详情页：标题/描述/创建者/时间 + 编辑/分享/加入/退出/删除按钮 |
| `ActivityEditView.vue` | 编辑活动页：修改标题和描述，仅创建者可访问 |
| `LoginView.vue` | 登录页 |
| `RegisterView.vue` | 注册页 |
| `ForgotPasswordView.vue` | 忘记密码：发送重置邮件 |
| `ResetPasswordView.vue` | 重置密码：通过 URL token 设置新密码 |
| `ChangePasswordView.vue` | 修改密码：旧密码+新密码 |
| `SettingsView.vue` | 个人设置：修改昵称、上传头像、注销账号 |
