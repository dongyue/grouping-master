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
| id | INT | PK, AUTO_INCREMENT | 主键 |
| user_id | INT | FK → users.id, NOT NULL, INDEX | 创建者 ID |
| title | VARCHAR(100) | NOT NULL | 活动标题 |
| description | TEXT | NULLABLE | 活动描述 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |
| updated_at | DATETIME | DEFAULT NOW() ON UPDATE NOW() | 更新时间 |

## 3. API 设计

### 3.1 API 端点

**认证接口**

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

**活动接口**

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| POST | `/api/activities` | Session | 创建活动 |
| GET | `/api/activities` | Session | 获取当前用户的活动列表（按创建时间倒序） |
| GET | `/api/activities/{id}` | Session | 查看活动详情（任意登录用户均可查看） |

> 活动列表和详情共用 `ActivityResponse` 响应格式：`{id, title, description, creator_nickname, created_at}`

### 3.2 认证机制

- 登录成功后服务端创建 Session（MySQL sessions 表），生成随机 session_id
- session_id 通过 `Set-Cookie` 返回，属性：`HttpOnly; SameSite=Lax; Max-Age=2592000`（30天）
- 后续请求自动携带 Cookie，中间件 `get_current_user` 校验 session_id 是否有效
- 登出时删除服务端 session，前端清除 Cookie

## 4. 安全策略

- 密码使用 bcrypt 哈希存储，不存明文
- Cookie 设为 HttpOnly 防 XSS，SameSite=Lax 防 CSRF
- 头像上传校验 MIME 类型和文件大小（2MB），UUID 重命名防遍历
- 忘记密码接口无论邮箱是否存在返回统一信息，防止用户枚举
- 重置密码后销毁该用户所有 Session，强制重新登录

## 5. 前端路由与页面

| 路径 | 页面 | 鉴权 | 说明 |
|------|------|------|------|
| `/login` | 登录页 | 仅未登录可访问 | 账号名 + 密码表单 |
| `/register` | 注册页 | 仅未登录可访问 | 注册表单（含确认密码） |
| `/forgot-password` | 忘记密码页 | 公开 | 输入邮箱发送重置链接 |
| `/reset-password` | 重置密码页 | 公开 | ?token=xxx，设置新密码 |
| `/` | 首页 | 需登录 | 创建活动表单 + 我的活动列表 |
| `/activities/:id` | 活动详情页 | 需登录 | 活动完整信息 + 分享按钮 |
| `/settings` | 设置页 | 需登录 | 头像上传、修改昵称、注销账号入口 |
| `/settings/change-password` | 修改密码页 | 需登录 | 旧密码 + 新密码表单 |
