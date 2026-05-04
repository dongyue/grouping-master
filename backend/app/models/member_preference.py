from sqlalchemy import Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class MemberPreference(Base):
    __tablename__ = "member_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("activity_members.id", ondelete="CASCADE"), nullable=False)
    target_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    preference_type: Mapped[str] = mapped_column(String(10), nullable=False)

    member = relationship("ActivityMember", back_populates="preferences")
    target_user = relationship("User")

    __table_args__ = (
        UniqueConstraint("member_id", "target_user_id", "preference_type", name="uq_member_target_type"),
    )
