import secrets
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


def _generate_slug() -> str:
    return secrets.token_hex(6)


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(12), unique=True, nullable=False, index=True, default=_generate_slug)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    group_strategy: Mapped[str] = mapped_column(String(20), nullable=False, default="fixed_group_size")
    group_param: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    constraints: Mapped[list | None] = mapped_column(JSON, nullable=True)
    allow_want_preferences: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_want_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    allow_avoid_preferences: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_avoid_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", lazy="joined")
