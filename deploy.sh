#!/bin/bash
# 部署脚本 — bash deploy.sh 运行，80 端口需 PORT=80 sudo -E bash deploy.sh
set -e

PORT="${PORT:-8000}"
BACKUP_DIR="frontend/dist.bak.$(date +%s)"
SUDO=""
if [ -n "$SUDO_USER" ]; then
    SUDO="sudo -u $SUDO_USER"
fi

echo ">>> 拉取最新代码..."
$SUDO git fetch
$SUDO git reset --hard origin/master

echo ">>> 安装依赖..."
cd frontend
$SUDO npm install
cd ..

echo ">>> 构建前端..."
cd frontend
if [ -d dist ]; then
    mv dist "../$BACKUP_DIR"
fi
$SUDO npm run build
cd ..

echo ">>> 数据库迁移..."
cd backend
venv/bin/alembic upgrade head

echo ">>> 重启后端..."
# 优雅关闭
pkill -TERM -f "uvicorn app.main:app" || true
sleep 2
# 强制清理残留
pkill -KILL -f "uvicorn app.main:app" || true
sleep 1

nohup venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "$PORT" </dev/null > uvicorn.log 2>&1 &
cd ..

# 等待启动
sleep 3
if curl -sf "http://localhost:$PORT/api/auth/config" > /dev/null 2>&1; then
    echo ">>> 部署完成"
    rm -rf "../$BACKUP_DIR" 2>/dev/null || true
else
    echo "!!! 健康检查失败，请查看 backend/uvicorn.log"
    if [ -d "../$BACKUP_DIR" ]; then
        mv "../$BACKUP_DIR" frontend/dist
        echo ">>> 已回滚前端构建产物"
    fi
    exit 1
fi
