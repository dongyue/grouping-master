import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import auth_router, activities_router
from app.config import FRONTEND_URL, UPLOAD_DIR

# 给 uvicorn 日志加上时间戳
log_format = "%(asctime)s %(levelname)-8s %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(log_format, datefmt=date_format)
for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
    for handler in logging.getLogger(name).handlers:
        handler.setFormatter(formatter)

app = FastAPI(title="分组大师", version="0.1.0")

# 开发环境允许 localhost 和 127.0.0.1
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(activities_router)

if os.path.exists(UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
