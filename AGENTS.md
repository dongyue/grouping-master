# 分组大师 - 开发指南

## 项目概述
分组大师是一个 SaaS 应用，前端 Vue 3，后端 FastAPI (Python)，数据库 MySQL 8.0。

## 开发工作流

**每次新功能开发严格按以下步骤执行：**

1. 从 master 拉出新的 feature 分支
2. 根据用户描述 → 编写/更新 `docs/requirements.md`，给用户确认
3. 用户确认后 → 编写/更新 `docs/design.md`，给用户确认
4. 用户确认后 → 编写代码，编写过程中运行 `python3 get_diff.py` 查看变更增量
5. 用户人工测试验收
 6. 验收通过后 → commit 所有改动 → 合入 master

### 文档定位

| 文档 | 位置 | 说明 |
|------|------|------|
| 需求文档 | `docs/requirements.md` | 功能需求、用户故事、验收标准（「做什么」）|
| 设计文档 | `docs/design.md` | 技术方案、数据库设计、API 设计、架构决策（「怎么做」）|

- 文档永远描述系统**全量**（当前完整状态），而非仅本次变更
- 与 master 的差异即反映本次功能的增量内容
- 新增功能时追加对应章节，重构时更新已有章节
- 文档不存在则创建
- 文档中禁止出现「新增」「调整为」「本次变更」等增量描述词。若设计变更了某处，直接写变更后的最终状态，不要单独标记那是变更
- **注意**：.env 不提交，.env.example 作为模板提交

### diff 工具

`python3 get_diff.py` 生成 `diff.md`，展示当前分支相对 master 的全部文件变更。

- 编写需求/设计文档时运行，了解已有文档和代码现状
- 编写代码时运行，了解增量变更
- **文档永远描述全量，diff 反映增量** — 两者互补

## 启动命令

### 后端
```bash
cd backend
# 首次运行：创建 .env 并配置数据库
cp .env.example .env
# 安装依赖
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
# 数据库迁移
alembic upgrade head
# 启动开发服务器（默认 8000 端口）
uvicorn app.main:app --reload
```

### 前端
```bash
cd frontend
npm install
npm run dev
```

## 目录结构

```
backend/                    # FastAPI 后端
├── app/
│   ├── main.py            # 应用入口，CORS 配置，路由注册
│   ├── config.py          # 环境变量配置（DB、SMTP、SECRET_KEY 等）
│   ├── database.py        # SQLAlchemy 引擎和 session
│   ├── models/            # 数据库模型（User、Session、PasswordReset）
│   ├── schemas/           # Pydantic 请求/响应校验
│   ├── routers/           # API 路由
│   ├── services/          # 业务逻辑（auth、mail）
│   └── middleware/        # 认证中间件（get_current_user 依赖注入）
└── alembic/               # 数据库迁移

frontend/                   # Vue 3 前端
└── src/
    ├── api/               # Axios 封装 + API 调用
    ├── stores/            # Pinia 状态管理（auth.js）
    ├── router/            # Vue Router + 路由守卫
    └── views/             # 页面组件
```

## 技术要点

- **认证方案**：服务端 Session（MySQL sessions 表）+ HttpOnly Cookie
- **密码哈希**：passlib + bcrypt
- **持久登录**：Session 默认保留 30 天（见 `app/config.py` 中 `SESSION_EXPIRE_DAYS`）
- **忘记密码**：通过 SMTP 发送重置邮件，token 有效期 30 分钟
- **头像上传**：本地文件系统，校验类型和大小（2MB），UUID 重命名防遍历
- **CSRF 防护**：Cookie `SameSite=Lax` + HttpOnly
- **前端鉴权**：Pinia store 启动时调 `GET /api/auth/me`，失败则跳转登录页

## 环境变量（必填）

| 变量 | 说明 |
|------|------|
| `DB_HOST/PORT/USER/PASSWORD/NAME` | MySQL 连接 |
| `SECRET_KEY` | Session 签名密钥 |
| `SMTP_HOST/PORT/USER/PASSWORD/FROM` | 邮件服务（找回密码用） |
| `FRONTEND_URL` | 前端地址（CORS + 重置密码链接） |

## 前端代理配置

前端 Axios 直接请求 `localhost:8000`，如需要代理，在 `vite.config.js` 中添加：
```js
server: { proxy: { '/api': 'http://localhost:8000' } }
```
并修改 `api/index.js` 中 `baseURL` 去除域名。
