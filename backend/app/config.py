import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "fenzudashi")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
SESSION_EXPIRE_DAYS = 30
# 以下上限前端也有对应常量，修改时需两端同步
MAX_CONSTRAINTS = 10
MAX_PREFERENCE_COUNT = 10
# 仅后端校验，前端无需同步
MAX_MEMBERS_PER_ACTIVITY = 500

SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@fenzudashi.com").strip()
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "true").lower() != "false"  # 默认 true，显式设 false 才跳过

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
AVATAR_DIR = os.path.join(UPLOAD_DIR, "avatars")
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

REQUIRE_PASSWORD = os.getenv("REQUIRE_PASSWORD", "true").lower() != "false"

RESET_TOKEN_EXPIRE_MINUTES = 30
