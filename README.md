# 分组大师 (Grouping Master)

智能分组利器——按自定义约束自动分组，支持手动拖拽调整，实时追踪成员变动。适用于团建、课程分组、住宿分配等场景。

## 功能

- **成员管理**：注册、登录、个人属性、活动加入/退出
- **自动分组**：固定每组人数/固定总组数两种策略
- **组内规则**：设定属性要求（如每组至少一位男生、部门不能重复等），分组时自动满足
- **成员偏好**：设置想/不想同组的人，算法作为软约束尽量满足
- **手动调整**：拖拽成员在组间移动、新增/删除组，自由不受限
- **变动日志**：分组后加入/退出/踢出的成员一目了然

## 截图

<!-- TODO: 替换为实际截图 -->
![首页](screenshots/home.png)
![活动详情页-分组前](screenshots/activity-before.png)
![活动详情页-分组后](screenshots/activity-after.png)

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3 + Vite + Pinia + Vue Router |
| 后端 | FastAPI + SQLAlchemy + Alembic |
| 数据库 | MySQL 8.0 |

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- MySQL 8.0

### 后端

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 编辑 .env 填写数据库连接等信息
alembic upgrade head
uvicorn app.main:app --reload
```

> 开发环境中如不需要真实发送邮件，可启动 Python 内置的调试 SMTP 服务器替代：
> ```bash
> python3 -m smtpd -c DebuggingServer -n localhost:1025
> ```
> 然后将 `.env` 中 `SMTP_HOST=localhost`、`SMTP_PORT=1025` 即可。邮件内容将打印在终端而非真实投递。

### 前端

```bash
cd frontend
npm install
npm run dev
```

默认访问 `http://localhost:5173`。

## 环境变量

在 `backend/.env` 中配置：

| 变量 | 说明 |
|------|------|
| `DB_HOST/PORT/USER/PASSWORD/NAME` | MySQL 连接信息 |
| `SECRET_KEY` | Session 签名密钥 |
| `SMTP_HOST/PORT/USER/PASSWORD/FROM` | 邮件服务（找回密码用） |
| `FRONTEND_URL` | 前端地址（CORS + 重置密码链接） |

## 目录结构

```
backend/                    # FastAPI 后端
├── app/
│   ├── main.py            # 应用入口
│   ├── config.py          # 配置常量
│   ├── database.py        # 数据库引擎
│   ├── models/            # ORM 模型
│   ├── schemas/           # 请求/响应校验
│   ├── routers/           # API 路由
│   ├── services/          # 业务逻辑（含分组算法）
│   └── middleware/         # 认证、限流
└── alembic/               # 数据库迁移

frontend/                   # Vue 3 前端
└── src/
    ├── api/               # Axios + API 调用
    ├── stores/            # Pinia 状态
    ├── router/            # 路由 + 鉴权守卫
    ├── components/        # 通用组件
    └── views/             # 页面组件
```

## 反馈与贡献

- 问题与建议：[GitHub Issues](https://github.com/dongyue/grouping-master/issues)
- 联系作者：me@dongyue.name

## 许可证

[GNU Affero General Public License v3.0](LICENSE.txt)
