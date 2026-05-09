import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.routers import auth_router, activities_router, members_router, groups_router, logs_router
from app.config import FRONTEND_URL, UPLOAD_DIR

logger = logging.getLogger("app")

# 给 uvicorn 日志加上时间戳
log_format = "%(asctime)s %(levelname)-8s %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(log_format, datefmt=date_format)
for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
    for handler in logging.getLogger(name).handlers:
        handler.setFormatter(formatter)

app = FastAPI(title="分组大师", version="0.1.0")

# CORS：开发环境允许 localhost，生产环境使用 FRONTEND_URL
origins = []
if os.getenv("CORS_ORIGINS"):
    origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else [],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+" if not origins else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(activities_router, prefix="/api/activities")
app.include_router(members_router, prefix="/api/activities")
app.include_router(groups_router, prefix="/api/activities")
app.include_router(logs_router, prefix="/api/activities")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("未处理的异常: %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误"},
    )

@app.on_event("startup")
async def startup_health():
    from app.database import SessionLocal
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        logger.info("数据库连接正常")
    except Exception as e:
        logger.critical("数据库连接失败: %s", e)

if os.path.exists(UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 生产环境：托管前端静态文件
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "frontend", "dist")
FRONTEND_DIST = os.path.normpath(FRONTEND_DIST)
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
