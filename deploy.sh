#!/bin/bash
set -e
echo ">>> 拉取最新代码..."
git pull

echo ">>> 安装依赖..."
cd frontend
npm install
cd ..

echo ">>> 构建前端..."
cd frontend
npm run build
cd ..

echo ">>> 数据库迁移..."
cd backend
venv/bin/alembic upgrade head

echo ">>> 重启后端..."
sudo pkill uvicorn || true
rm -f nohup.out
sudo nohup venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 80 > /dev/null 2>&1 &
cd ..

echo ">>> 部署完成"
