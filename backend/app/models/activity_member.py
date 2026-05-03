from datetime import datetime
from sqlalchemy import ForeignKey, Integer, DateTime, UniqueConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ActivityMember(Base):
    __tablename__ = "activity_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    activity = relationship("Activity", lazy="joined")
    user = relationship("User", lazy="joined")

    __table_args__ = (
        UniqueConstraint("activity_id", "user_id", name="uq_activity_user"),
    )
