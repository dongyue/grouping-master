# 代码库地图

> 列出项目中所有源码文件及其职责，方便 AI 快速定位。

## 后端（backend/）

### 应用入口

| 文件 | 职责 |
|------|------|
| `app/main.py` | FastAPI 入口：CORS 配置、静态文件挂载、路由注册 |
| `app/config.py` | 读取 `.env`，导出数据库/SMTP/Session/上传目录/密码要求等全局配置 |
| `app/database.py` | SQLAlchemy 引擎/Session 工厂、`Base` 基类、`get_db` 依赖注入 |

### ORM 模型（app/models/）

| 文件 | 职责 |
|------|------|
| `__init__.py` | 汇总导出所有模型 |
| `user.py` | `User` 表：id, username, nickname, password_hash, email, avatar_path, 时间戳 |
| `session.py` | `Session` 表：服务端 session 持久化（id, user_id, data, expires_at） |
| `password_reset.py` | `PasswordReset` 表：密码重置令牌（token, expires_at, used） |
| `activity.py` | `Activity` 表：活动（id, slug, user_id FK, title, description, group_strategy, group_param, constraints JSON, 时间戳），关联 User |
| `activity_member.py` | `ActivityMember` 表：活动成员关系（id, activity_id FK, user_id FK, 时间戳），联合唯一约束 |
| `group.py` | `Group` 表：分组（id, activity_id FK, group_number, 时间戳），关联 GroupMember |
| `group_member.py` | `GroupMember` 表：分组成员关系（id, group_id FK, user_id FK），联合唯一约束 |
| `member_attribute.py` | `MemberAttribute` 表：成员属性值（id, member_id FK, attribute_name, attribute_value），联合唯一约束，ON DELETE CASCADE，通过 backref `attributes` 反向关联 ActivityMember |

### Pydantic Schema（app/schemas/）

| 文件 | 职责 |
|------|------|
| `__init__.py` | 汇总导出所有 schema |
| `auth.py` | 全部请求/响应校验：注册、登录、改密、重置密码、更新资料、头像、注销、创建活动、更新活动、加入活动（含属性值）、活动列表、活动详情、成员列表、分组结果、组内多样性限定规则 |

### API 路由（app/routers/）

| 文件 | 职责 |
|------|------|
| `__init__.py` | 汇总导出路由 |
| `auth.py` | `/api/auth/*` — 注册/登录/登出/me/改密/忘记密码/重置密码/更新资料/头像/注销账号 |
| `activities.py` | `/api/activities` — POST 创建、GET 列表、GET `/:slug` 详情、POST `/:slug` 加入/退出、PUT `/:slug` 编辑、DELETE `/:slug` 删除、DELETE `/:slug/members/:user_id` 踢出成员、POST `/:slug/groups` 分组（含重新分组）、DELETE `/:slug/groups` 解除分组 |

### 业务服务（app/services/）

| 文件 | 职责 |
|------|------|
| `__init__.py` | 汇总导出业务函数 |
| `auth.py` | 密码哈希/校验、注册/登录、Session 创建/查询/删除、密码重置令牌生成 |
| `mail.py` | SMTP 邮件发送（`send_reset_email`）、随机令牌生成 |
| `upload.py` | 文件魔术头校验（`validate_magic_bytes`），防伪造 MIME 类型上传 |

### 中间件（app/middleware/）

| 文件 | 职责 |
|------|------|
| `__init__.py` | 导出 `get_current_user`、`RateLimiter` |
| `auth.py` | `get_current_user` 依赖注入：从 Cookie session_id 校验并返回当前 User |
| `rate_limit.py` | `RateLimiter` 类：基于 IP + 路径的请求频率限制，窗口 60 秒，用于登录/注册/忘记密码接口 |

### 数据库迁移（alembic/）

| 文件 | 职责 |
|------|------|
| `env.py` | Alembic 引擎配置，关联 Base.metadata |
| `versions/802b0df17e93_init.py` | 初始迁移：users、sessions、password_resets 三表 |
| `versions/4ebf2b01b301_add_activities_table.py` | 新增 activities 表 |
| `versions/4373c7646a4b_add_activity_members_table.py` | 新增 activity_members 表 |
| `versions/d9158a7c8e2f_add_slug_to_activities.py` | activities 表新增 slug 列 |
| `versions/5a1b2c3d4e5f_add_groups_and_group_members.py` | 新增 groups 表和 group_members 表 |
| `versions/6b2c3d4e5f6a_add_group_strategy_to_activities.py` | activities 表新增 group_strategy、group_param、remainder_handling 字段 |
| `versions/7c3d4e5f6a7b_remove_remainder_handling.py` | activities 表删除 remainder_handling 字段 |
| `versions/8d4e5f6a7b8c_add_constraints_to_activities.py` | activities 表新增 constraints JSON 字段 |
| `versions/9e5f6a7b8c9d_add_member_attributes_table.py` | 新增 member_attributes 表 |

---

## 前端（frontend/src/）

### 入口与路由

| 文件 | 职责 |
|------|------|
| `main.js` | Vue 3 入口：创建 Pinia、Router，挂载 `#app` |
| `App.vue` | 根组件：顶部导航栏 + `<router-view>` + 全局按钮样式（btn-primary/secondary/warning/danger） |
| `style.css` | CSS reset 与字体渲染优化 |
| `router/index.js` | 路由表 + `beforeEach` 鉴权守卫 + 登录重定向 + 404 兜底路由 |

### API 调用层（api/）

| 文件 | 职责 |
|------|------|
| `index.js` | Axios 实例：baseURL、withCredentials、响应/错误拦截器 |
| `auth.js` | 认证 API：注册/登录/登出/me/改密/忘记密码/重置密码/更新资料/头像/注销 |
| `activities.js` | 活动 API：createActivity、listActivities、getActivity、joinActivity、leaveActivity、updateActivity、deleteActivity、kickMember、createGroups、deleteGroups |

### 状态管理（stores/）

| 文件 | 职责 |
|------|------|
| `auth.js` | Pinia store：user 状态、isLoggedIn、fetchUser/login/logout |

### 工具函数（utils/）

| 文件 | 职责 |
|------|------|
| `date.js` | `formatDate` 统一日期格式化为 YYYY-MM-DD |
| `groupRule.js` | 分组策略选项列表与标签映射，供表单和详情页共用 |
| `constraintPresets.js` | 组内多样性限定预设属性名列表，供 ConstraintEditor 和编辑页回显共用 |

### 通用组件（components/）

| 文件 | 职责 |
|------|------|
| `ConstraintEditor.vue` | 组内多样性限定规则编辑器：下拉选择/自定义属性名、动态增删规则、自动填入枚举值、校验限定值范围，供创建/编辑活动页复用 |
| `AttributeSelector.vue` | 属性选择弹框：成员加入活动时选择各属性的值，以弹框形式展示，全部必填，供详情页加入流程复用 |
| `ConfirmModal.vue` | 确认对话框组件，供退出活动、删除活动、踢出成员、解除分组、注销账号等危险操作确认复用 |

### 页面组件（views/）

| 文件 | 职责 |
|------|------|
| `HomeView.vue` | 首页：「我创建的活动」列表（含「创建活动」按钮入口）+「我加入的活动」列表，按创建时间倒序 |
| `CreateActivityView.vue` | 创建活动页：活动标题、描述、「分组规则」区域（分组方式配置 + 组内多样性限定）、创建者参加复选框 |
| `ActivityDetailView.vue` | 活动详情页：操作按钮（加入活动/开始分组 + 分享链接 + 更多▼）+ 分组规则展示 + 成员列表（分组/尚未分组/平铺三视图）+ 踢出成员（管理成员开关）+ 属性选择弹框 + 确认对话框；重新分组/解除分组/编辑/删除在更多菜单中 |
| `ActivityEditView.vue` | 编辑活动页：修改标题、描述、「分组规则」区域（分组方式配置 + 组内多样性限定），仅创建者可访问，取消回到详情页 |
| `LoginView.vue` | 登录页 |
| `RegisterView.vue` | 注册页（通过 API 获取密码要求配置，决定表单是否显示密码字段） |
| `ForgotPasswordView.vue` | 忘记密码：发送重置邮件 |
| `ResetPasswordView.vue` | 重置密码：通过 URL token 设置新密码（含确认密码输入框） |
| `ChangePasswordView.vue` | 修改密码：旧密码+新密码+确认新密码 |
| `SettingsView.vue` | 个人设置：修改昵称、上传头像、注销账号 |
| `NotFoundView.vue` | 404 页面：提示页面不存在，提供返回首页入口 |
