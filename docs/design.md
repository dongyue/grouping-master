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
| group_strategy | VARCHAR(20) | NOT NULL, DEFAULT 'fixed_group_size' | 分组策略：`fixed_group_size`（固定每组人数）、`fixed_group_count`（固定总组数） |
| group_param | INT | NOT NULL, DEFAULT 2 | 策略参数：`fixed_group_size` 时表示每组人数；`fixed_group_count` 时表示目标组数 |
| constraints | JSON | NULLABLE | 多样性限定规则列表，结构见 2.8 |
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

### 2.8 member_attributes 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| member_id | INT | FK → activity_members.id, NOT NULL, ON DELETE CASCADE | 成员记录 ID |
| attribute_name | VARCHAR(100) | NOT NULL | 属性名 |
| attribute_value | VARCHAR(100) | NOT NULL | 属性值 |

> 联合唯一约束：(member_id, attribute_name)，每个成员的每个属性只能有一个值
> member_id 设置 ON DELETE CASCADE：成员退出/被踢出时属性值同步删除

### 2.9 activity_logs 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| activity_id | INT | FK → activities.id, NOT NULL, INDEX | 活动 ID |
| user_id | INT | FK → users.id, NOT NULL | 操作人 ID |
| action_type | VARCHAR(30) | NOT NULL | 操作类型（create/edit/join/leave/kick/group/ungroup） |
| content | TEXT | NOT NULL | 操作内容描述 |
| detail | JSON | NULLABLE | 结构化详情数据（分组操作时记录快照） |
| created_at | DATETIME | DEFAULT NOW() | 操作时间 |

### 2.10 constraints 字段结构

activities 表的 `constraints` 字段为 JSON 数组，每项为一条多样性限定规则：

```json
[
  {
    "attribute_name": "性别",
    "allowed_values": ["男", "女"],
    "constraint_type": "min_diversity",
    "constraint_value": 2
  }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `attribute_name` | str | 属性名，同一活动内不可重复 |
| `allowed_values` | list[str] | 属性值枚举，至少 2 个值 |
| `constraint_type` | str | `"min_diversity"`（限定最小多样性）或 `"max_diversity"`（限定最大多样性） |
| `constraint_value` | int | 限定值。限定最小值时满足 2 ≤ value ≤ len(allowed_values)；限定最大值时满足 1 ≤ value ≤ len(allowed_values)-1 |

## 3. API 设计

### 3.1 认证接口

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| GET | `/api/auth/config` | 无 | 获取认证配置（如密码是否必填） |
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

**注册密码要求**
- `.env` 中 `REQUIRE_PASSWORD` 控制注册时是否必须设置密码（默认 `true`）
- 前端通过 `GET /api/auth/config` 获取该配置，动态决定注册表单是否显示密码字段
- `true`（默认）：密码必填，至少 8 位
- `false`（调试用）：密码可选，不填密码的用户登录时无需密码

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
| GET | `/api/activities/{slug}/logs` | Session | 查看操作日志（仅创建者） |

`POST /api/activities` 创建活动
- 请求体：`{title: str, description?: str, group_strategy?: str, group_param?: int, constraints?: list[ConstraintRule]}`
- `group_strategy` 默认 `"fixed_group_size"`，可选 `"fixed_group_size"`（固定每组人数）、`"fixed_group_count"`（固定总组数）
- `group_param` 默认 `2`，最小值 `2`，含义由 `group_strategy` 决定
- `constraints` 为多样性限定规则列表，可选，不传或传空数组表示不限定
- 创建时自动生成 12 位随机 slug，作为活动公网标识

`GET /api/activities?type=created|joined`
- `type=created` 返回当前用户创建的活动列表
- `type=joined` 返回当前用户加入的活动列表
- 均按创建时间倒序

`GET /api/activities/{slug}`
- 响应字段：`{id, slug, title, description, group_strategy, group_param, constraints, creator_nickname, created_at, is_member, is_creator, has_groups, groups, members, ungrouped_members}`
- `constraints`：`[ConstraintRule]` 多样性限定规则列表，空数组表示无限定
- `groups`：`[GroupResponse]` 分组列表，未分组时为空数组。每项 `{group_number, members: [MemberItem]}`
- `members`：`[MemberItem]` 成员列表，每项 `{user_id, nickname, avatar_path, joined_at, attributes}`，其中 `attributes` 为 `Record<string, string>`，按加入时间升序
- `ungrouped_members`：`[MemberItem]` 尚未分组的成员列表。未分组时为空数组，分组后包含未分配到任何组的成员

`POST /api/activities/{slug}/join`
- 请求体：`JoinActivityRequest {attribute_values?: Record<string, string>}`
- 活动有约束规则时，`attribute_values` 必填，须包含全部属性名，每个值须在对应属性的允许值列表内
- 活动无约束规则时，`attribute_values` 可省略或为 `null`，直接加入
- 用户已加入时返回 409
- 响应：`{message: "加入成功"}`

`DELETE /api/activities/{slug}`
- 仅活动创建者可删除
- 非创建者返回 403
- 活动不存在返回 404
- 数据库已配置 ON DELETE CASCADE，删除活动时成员关系自动清除
- 响应：`{message: "活动已删除"}`

`POST /api/activities/{slug}/leave`
- 无请求体
- 用户未加入活动时返回 409
- 若已分组，同步删除该成员在各组中的记录

`PUT /api/activities/{slug}`
- 请求体：`{title: str, description?: str, group_strategy?: str, group_param?: int, constraints?: list[ConstraintRule]}`
- 仅活动创建者可更新
- 非创建者返回 403
- 响应：更新后的 `ActivityResponse`

`DELETE /api/activities/{slug}/members/{user_id}`
- 无请求体
- 仅活动创建者可踢出成员
- 非创建者返回 403
- 目标用户不是该活动成员时返回 404
- 创建者不能踢出自己，返回 400
- 若已分组，同步删除该成员在各组中的记录
- 响应：`{message: "已将该成员移出活动"}`

`POST /api/activities/{slug}/groups`
- 无请求体
- 仅活动创建者可执行，非创建者返回 403
- 若已分组，先清除已有分组及组成员数据，再重新分组
- 读取活动的 `group_strategy`、`group_param` 配置执行分组
- `group_strategy = "fixed_group_size"`：成员随机打乱，按 `group_param` 人一组分配。若不能整除，最后不足一组的人数归入「尚未分组」不分配
- `group_strategy = "fixed_group_count"`：成员随机打乱，尽可能平均分配到 `group_param` 组（每组 `floor(总人数/组数)` 人）。余数归入「尚未分组」
- 响应：`{groups: [GroupResponse], ungrouped_members: [MemberItem]}`

`DELETE /api/activities/{slug}/groups`
- 无请求体
- 仅活动创建者可执行
- 非创建者返回 403
- 活动未分组时返回 404
- 删除该活动下所有分组及成员关系，活动恢复未分组状态
- 响应：`{message: "已解除分组"}`

`GET /api/activities/{slug}/logs`
- 无请求体
- 仅活动创建者可查看，非创建者返回 403
- 响应：`list[ActivityLogResponse]`，按时间倒序
- `ActivityLogResponse` 字段：`{id, user_nickname, action_type, content, detail, created_at}`
- `detail` 为 JSON 对象（可为 null），仅在 `action_type` 为 `group` 时包含结构化分组快照：
  - `activity_snapshot`：{group_strategy, group_param, constraints}
  - `members`：[{user_id, nickname, attributes: Record<string, string>}] 分组时所有成员及其属性
  - `seed`：随机种子（用于复现分组结果）
  - `shuffle_order`：[user_id] 打乱前的成员顺序
  - `groups`：[{group_number, members: [{user_id, nickname}]}] 分组结果
  - `ungrouped`：[{user_id, nickname}] 尚未分组成员

> 活动列表项响应格式：`{id, slug, title, description, group_strategy, group_param, constraints, creator_nickname, created_at}`

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
| `/` | 首页 | 需登录 | 「我创建的活动」列表（含「创建活动」按钮）+「我加入的活动」列表 |
| `/activities/create` | 创建活动页 | 需登录 | 活动标题、描述、「我作为创建者也要参加」复选框（默认勾选）、「分组规则」区域（含分组方式配置、组内多样性限定规则） |
| `/activities/:slug` | 活动详情页 | 需登录 | 主行：加入活动（未加入用户）/ 开始分组（创建者，未分组时）+ 分享链接 + 更多 ▼；更多菜单：退出活动（已加入成员）+ 重新分组（创建者，已分组时）+ 解除分组（创建者，已分组时）+ 编辑活动（创建者）+ 查看日志（创建者）+ 删除活动（创建者）；「分组规则」标题下展示分组方式与逐条多样性限定；成员列表（未分组时平铺，已分组后按组展示，标题显示总人数与组数） |
| `/activities/:slug/logs` | 操作日志页 | 需登录 | 展示该活动所有操作日志，按时间倒序；分组日志可展开查看快照详情；仅创建者可访问，非创建者重定向到活动详情页 |
| `/activities/:slug/edit` | 编辑活动页 | 需登录 | 编辑活动标题、描述、「分组规则」区域（含分组方式配置、组内多样性限定规则），仅创建者可操作，非创建者重定向回详情页 |
| `/settings` | 设置页 | 需登录 | 头像上传、修改昵称、注销账号入口 |
| `/settings/change-password` | 修改密码页 | 需登录 | 旧密码 + 新密码 + 确认新密码表单 |

## 6. 前端工具与组件

### 6.1 确认对话框组件
- 新建 `ConfirmModal.vue`，全局注册或按需引入
- 提供确认/取消按钮，支持自定义标题和内容
- 替代所有原生 `confirm()` 调用

### 6.2 日期格式化工具
- 新建 `utils/date.js`，提供 `formatDate` 函数，统一输出 `YYYY-MM-DD` 格式
- 所有页面中日期显示均通过该函数

### 6.3 404 页面
- 新建 `NotFoundView.vue`，路由末尾添加 `/:pathMatch(.*)*` 匹配

### 6.4 登录重定向
- 路由守卫 `beforeEach` 中将目标路径存为 `redirect` query 参数
- 登录页/注册页在登录/注册成功后跳转回 `redirect` 目标

### 6.5 前端环境变量
- API 基地址通过 `.env` 变量 `VITE_API_BASE_URL` 配置（默认 `/api`），头像资源地址通过 `.env` 变量 `VITE_UPLOADS_URL` 配置
- Vite 开发服务器配置代理 `/api` → `http://localhost:8000`，避免跨域问题
- 前端 Axios 通过 `withCredentials: true` 携带 Cookie

### 6.6 组内多样性限定编辑器
- 新建 `ConstraintEditor.vue`，封装组内多样性限定规则的增删改 UI
- 属性名支持下拉选择预设值（性别、团队、部门、单位、班级、年级、学校）+ 自定义输入
- 选择「性别」时自动填入枚举值「男，女」
- 限定值输入框根据 constrained_type 动态限制 min/max
- 供创建活动页和编辑活动页复用

### 6.7 属性选择弹框
- 新建 `AttributeSelector.vue`，以弹框形式展示，供成员加入活动时选择各属性值
- 接收活动的 `constraints` 数组，为每条规则渲染控件：
  - 属性名作为标签，属性值通过下拉选择（选项为对应的 `allowed_values`）
- 所有属性均为必填，提交前校验
- 提交时以 `Record<string, string>` 格式向 join 接口传递
- 供活动详情页和创建活动后的加入流程复用

### 6.8 操作日志页
- 新建 `ActivityLogsView.vue`，按时间倒序展示日志列表
- 每条日志显示：操作人昵称、操作内容描述、操作时间
- 分组类型日志额外显示「展开详情」按钮，点击展开结构化快照（分组规则快照、成员列表、分组结果、尚未分组列表）
- 日志页面仅活动创建者可访问，非创建者重定向回详情页
