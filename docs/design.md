# 分组大师 - 设计文档

## 1. 技术栈

| 层 | 选型 | 版本 |
|------|------|------|
| 前端 | Vue 3 + Vite | 3.x |
| 状态管理 | Pinia | 2.x |
| 路由 | Vue Router | 4.x |
| HTTP 客户端 | Axios | 1.x |
| 后端 | FastAPI | 0.115+ |
| ORM | SQLAlchemy | 2.0 |
| 数据库迁移 | Alembic | 1.13 |
| 密码哈希 | passlib + bcrypt | 1.7 |
| 数据库 | MySQL | 8.0 |

## 2. 数据库设计

### 2.1 users 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| username | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | 账号名 |
| nickname | VARCHAR(50) | NOT NULL | 昵称 |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 哈希 |
| email | VARCHAR(100) | UNIQUE, NULLABLE | 备用邮箱 |
| avatar_path | VARCHAR(255) | NULLABLE | 头像相对路径 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |
| updated_at | DATETIME | DEFAULT NOW() ON UPDATE NOW() | 更新时间 |

### 2.2 sessions 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(128) | PK | session_id |
| user_id | INT | FK → users.id, NOT NULL, INDEX | 用户 ID |
| data | TEXT | NULLABLE | session 数据（JSON） |
| expires_at | DATETIME | NOT NULL | 过期时间 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |

### 2.3 password_resets 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| user_id | INT | FK → users.id, NOT NULL | 用户 ID |
| token | VARCHAR(64) | UNIQUE, NOT NULL, INDEX | 重置令牌 |
| expires_at | DATETIME | NOT NULL | 过期时间（30 分钟） |
| used | BOOLEAN | DEFAULT FALSE | 是否已使用 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |

### 2.4 activities 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 主键（内部使用） |
| slug | VARCHAR(12) | UNIQUE, NOT NULL, INDEX | 公网标识（URL 中使用） |
| user_id | INT | FK → users.id, NOT NULL, INDEX | 创建者 ID |
| title | VARCHAR(100) | NOT NULL | 活动标题 |
| description | TEXT | NULLABLE | 活动描述 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |
| updated_at | DATETIME | DEFAULT NOW() ON UPDATE NOW() | 更新时间 |

### 2.5 activity_members 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| activity_id | INT | FK → activities.id, NOT NULL | 活动 ID |
| user_id | INT | FK → users.id, NOT NULL | 成员 ID |
| created_at | DATETIME | DEFAULT NOW() | 加入时间 |

> 联合唯一约束：(activity_id, user_id)，防止重复加入

### 2.6 groups 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| activity_id | INT | FK → activities.id, NOT NULL, INDEX | 活动 ID |
| group_number | INT | NOT NULL | 组号（从 1 开始递增） |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |

### 2.7 group_members 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| group_id | INT | FK → groups.id, NOT NULL | 组 ID |
| user_id | INT | FK → users.id, NOT NULL | 成员 ID |

> 联合唯一约束：(group_id, user_id)，防止重复分配

## 3. API 设计

### 3.1 认证接口

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| POST | `/api/auth/register` | 无 | 注册 |
| POST | `/api/auth/login` | 无 | 登录 |
| POST | `/api/auth/logout` | Session | 登出 |
| GET | `/api/auth/me` | Session | 获取当前用户 |
| PUT | `/api/auth/password` | Session | 修改密码 |
| POST | `/api/auth/forgot-password` | 无 | 发送重置邮件 |
| POST | `/api/auth/reset-password` | 无 | 重置密码 |
| PUT | `/api/auth/profile` | Session | 更新个人资料 |
| POST | `/api/auth/avatar` | Session | 上传头像 |
| DELETE | `/api/auth/account` | Session | 注销账号 |

**认证机制**

- 登录成功后服务端创建 Session（MySQL sessions 表），生成随机 session_id
- session_id 通过 `Set-Cookie` 返回，属性：`HttpOnly; SameSite=Lax; Max-Age=2592000`（30天）
- 后续请求自动携带 Cookie，中间件 `get_current_user` 校验 session_id 是否有效
- 登出时删除服务端 session，前端清除 Cookie

### 3.2 活动接口

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| POST | `/api/activities` | Session | 创建活动 |
| GET | `/api/activities` | Session | 获取活动列表（按 `type` 参数返回 `created` 或 `joined`） |
| GET | `/api/activities/{slug}` | Session | 查看活动详情（任意登录用户均可查看） |
| POST | `/api/activities/{slug}/join` | Session | 加入活动 |
| DELETE | `/api/activities/{slug}` | Session | 删除活动（仅创建者） |
| POST | `/api/activities/{slug}/leave` | Session | 退出活动 |
| PUT | `/api/activities/{slug}` | Session | 更新活动（仅创建者） |
| DELETE | `/api/activities/{slug}/members/{user_id}` | Session | 踢出成员（仅创建者） |
| POST | `/api/activities/{slug}/groups` | Session | 执行分组（仅创建者） |
| DELETE | `/api/activities/{slug}/groups` | Session | 解除分组（仅创建者） |

`POST /api/activities` 创建活动
- 请求体：`{title: str, description?: str, join_activity?: bool}`
- `join_activity` 默认 `true`，为 `true` 时创建者同时加入活动
- 创建时自动生成 12 位随机 slug，作为活动公网标识

`GET /api/activities?type=created|joined`
- `type=created` 返回当前用户创建的活动列表
- `type=joined` 返回当前用户加入的活动列表
- 均按创建时间倒序

`GET /api/activities/{slug}`
- 响应字段：`{id, slug, title, description, creator_nickname, created_at, is_member, is_creator, groups, members}`
- `is_member`：当前用户是否已加入该活动
- `is_creator`：当前用户是否为该活动创建者
- `groups`：`[GroupResponse]` 分组列表，未分组时为空数组。每项 `{group_number, members: [MemberItem]}`
- `members`：`[MemberItem]` 成员列表，每项 `{user_id, nickname, avatar_path, joined_at}`，按加入时间升序

`POST /api/activities/{slug}/join`
- 无请求体
- 用户已加入时返回 409
- 活动已分组时返回 409

`DELETE /api/activities/{slug}`
- 仅活动创建者可删除
- 非创建者返回 403
- 活动不存在返回 404
- 数据库已配置 ON DELETE CASCADE，删除活动时成员关系自动清除
- 响应：`{message: "活动已删除"}`

`POST /api/activities/{slug}/leave`
- 无请求体
- 用户未加入活动时返回 409
- 活动已分组时返回 409

`PUT /api/activities/{slug}`
- 请求体：`{title: str, description?: str}`
- 仅活动创建者可更新
- 非创建者返回 403
- 响应：更新后的 `ActivityResponse`

`DELETE /api/activities/{slug}/members/{user_id}`
- 无请求体
- 仅活动创建者可踢出成员
- 非创建者返回 403
- 目标用户不是该活动成员时返回 404
- 创建者不能踢出自己，返回 400
- 活动已分组时返回 409
- 响应：`{message: "已将该成员移出活动"}`

`POST /api/activities/{slug}/groups`
- 无请求体
- 仅活动创建者可执行
- 非创建者返回 403
- 将当前活动成员随机打乱，按每组 2 人分配，剩余 1 人则单独成组
- 响应：`{groups: [GroupResponse]}`，每组含 `group_number` 和 `members` 列表

`DELETE /api/activities/{slug}/groups`
- 无请求体
- 仅活动创建者可执行
- 非创建者返回 403
- 活动未分组时返回 404
- 删除该活动下所有分组及成员关系，活动恢复未分组状态
- 响应：`{message: "已解除分组"}`

> 活动列表项响应格式：`{id, slug, title, description, creator_nickname, created_at}`

## 4. 安全策略

- 密码使用 bcrypt 哈希存储，不存明文
- Cookie 设为 HttpOnly 防 XSS，SameSite=Lax 防 CSRF
- 头像上传校验 MIME 类型、文件魔术头和文件大小（2MB），UUID 重命名防遍历
- 忘记密码接口无论邮箱是否存在返回统一信息，防止用户枚举
- 重置密码后销毁该用户所有 Session，强制重新登录
- 活动使用随机 slug 替代自增 ID 暴露在 URL 中，防止枚举遍历
- 登录、注册、忘记密码接口实施 IP 级别速率限制，防暴力破解

### 4.1 速率限制

| 接口 | 限制 | 超限响应 |
|------|------|----------|
| `POST /api/auth/login` | 同 IP 每分钟 5 次 | 429 Too Many Requests |
| `POST /api/auth/register` | 同 IP 每分钟 5 次 | 429 Too Many Requests |
| `POST /api/auth/forgot-password` | 同 IP 每分钟 5 次 | 429 Too Many Requests |

- 基于 FastAPI `Depends` 依赖注入实现，仅限目标路由
- 限流数据存于应用内存，基于 IP + 接口路径计数，滑动窗口 60 秒
- 服务重启后清零，不持久化

### 4.2 头像文件魔术头校验

| 类型 | 魔术头 (hex) |
|------|-------------|
| JPEG | `FF D8 FF` |
| PNG | `89 50 4E 47` |
| GIF | `47 49 46 38` |

- 在上传头像时，除 MIME 类型检查外，校验文件二进制前若干字节
- 校验不通过返回 400，防止伪造 Content-Type 上传恶意文件

## 5. 前端路由与页面

| 路径 | 页面 | 鉴权 | 说明 |
|------|------|------|------|
| `/login` | 登录页 | 仅未登录可访问 | 账号名 + 密码表单 |
| `/register` | 注册页 | 仅未登录可访问 | 注册表单（含确认密码） |
| `/forgot-password` | 忘记密码页 | 公开 | 输入邮箱发送重置链接 |
| `/reset-password` | 重置密码页 | 公开 | ?token=xxx，设置新密码 |
| `/` | 首页 | 需登录 | 创建活动表单（含「同时加入活动」复选框） + 「我创建的活动」列表 + 「我加入的活动」列表 |
| `/activities/:slug` | 活动详情页 | 需登录 | 活动完整信息 + 编辑按钮（创建者）+ 分组/解除分组按钮（创建者）+ 分享按钮 + 加入/退出按钮（活动未分组时显示）+ 删除按钮 + 踢出成员（创建者可操作，活动未分组时显示）+ 成员列表（未分组时平铺，已分组后按组展示，标题显示总人数与组数） |
| `/activities/:slug/edit` | 编辑活动页 | 需登录 | 编辑活动标题和描述，仅创建者可操作，非创建者重定向回详情页 |
| `/settings` | 设置页 | 需登录 | 头像上传、修改昵称、注销账号入口 |
| `/settings/change-password` | 修改密码页 | 需登录 | 旧密码 + 新密码表单 |
