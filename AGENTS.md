# 分组大师 - 开发指南

## 项目概述
分组大师是一个 SaaS 应用，前端 Vue 3，后端 FastAPI (Python)，数据库 MySQL 8.0。

## 开发工作流

**凡是涉及源代码的改动，严格按以下步骤执行。需用户确认的步骤，必须经用户确认后方可进入下一步，严禁跳步。**

0. 用户与 AI 讨论需求：AI 复述自身理解、评估合理性、给出建议，直至用户认为 OK
1. 从 master 拉出新的 feature 分支
2. 编写/更新 `docs/requirements.md`，给用户确认
3. 用户确认后 → 编写/更新 `docs/design.md`，给用户确认
4. 用户确认后 → 编写代码
5. 用户人工测试验收
6. 验收通过后 → 检查并更新 `docs/requirements.md`、`docs/design.md`、`docs/codebase-map.md`，确保三者反映当前源代码功能，给用户确认
7. 用户确认后 → commit 所有改动 → 合入 master

### 文档定位

| 文档 | 位置 | 说明 |
|------|------|------|
| 需求文档 | `docs/requirements.md` | 功能需求、用户故事、验收标准（「做什么」）|
| 设计文档 | `docs/design.md` | 技术方案、数据库设计、API 设计、架构决策（「怎么做」）|
| 代码库地图 | `docs/codebase-map.md` | 全部源码文件路径与职责，AI 快速定位用 |

- 文档永远描述系统**全量**（当前完整状态），而非仅本次变更
- 与 master 的差异即反映本次功能的增量内容
- 新增功能时追加对应章节，重构时更新已有章节
- 新增/删除/重命名文件，或文件职责发生变化时，同步更新 `docs/codebase-map.md`
- 文档不存在则创建
- 文档中禁止出现「新增」「调整为」「本次变更」等增量描述词。若设计变更了某处，直接写变更后的最终状态，不要单独标记那是变更
- **注意**：.env 不提交，.env.example 作为模板提交

### diff 工具

`python3 get_diff.py` 生成 `diff.md`，展示当前 feature 分支相对本地 master 分支末端的全部变更。

- 编写需求文档时，必要时运行，了解已撰写的需求和文档
- 编写设计文档时，必要时运行，了解已撰写的需求与设计
- 编写代码时，必要时运行，了解已撰写的需求、设计及已完成的代码改动
- 代码完成后，必要时运行，检查需求、设计、代码改动三者是否一致

- **文档永远描述全量，diff 反映增量** — 两者互补

### 代码探索原则

理解现有代码时，**文档优先，按需读源码**：

1. 先读 `docs/requirements.md` — 了解相关功能需求
2. 再读 `docs/design.md` — 了解数据库设计、API 设计、技术方案
3. 再读 `docs/codebase-map.md` — 定位需要改动的文件
4. 最后，只读要改的文件，不批量读取无关模块

三个文档是系统全量状态的唯一真相源，大规模源码探索是冗余的。

### Edit 工具使用规范

使用 Edit 工具替换文本时，避免 `oldString not found` 错误：

1. **匹配字符串尽量短且唯一** — 长句子易因隐藏编码差异（中文标点、全角/半角空格）导致不匹配，只用足以唯一定位的最小片段
2. **涉及中文/特殊符号时，先用 `cat -A` 校核目标行原始字节** — 显式展示不可见字符和编码差异
3. **优先使用 `replaceAll` 做全局替换** — 不受上下文唯一性限制，适合变量名/函数名全局重命名
4. **匹配失败时先用 `grep -n` 输出精确行号和内容** — 复制实际输出作为 `oldString`，避免凭印象构造

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
│   ├── config.py          # 环境变量配置
│   ├── database.py        # SQLAlchemy 引擎和 session
│   ├── models/            # ORM 数据库模型
│   ├── schemas/           # Pydantic 请求/响应校验
│   ├── routers/           # API 路由
│   ├── services/          # 业务逻辑
│   └── middleware/        # 中间件（依赖注入、限流等）
└── alembic/               # 数据库迁移

frontend/                   # Vue 3 前端
└── src/
    ├── api/               # Axios 封装 + API 调用
    ├── stores/            # Pinia 状态管理
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
