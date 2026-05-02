from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref
from app.database import Base


class MemberAttribute(Base):
    __tablename__ = "member_attributes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("activity_members.id", ondelete="CASCADE"), nullable=False)
    attribute_name: Mapped[str] = mapped_column(String(100), nullable=False)
    attribute_value: Mapped[str] = mapped_column(String(100), nullable=False)

    member = relationship("ActivityMember", backref=backref("attributes", passive_deletes=True))

    __table_args__ = (
        UniqueConstraint("member_id", "attribute_name", name="uq_member_attribute"),
    )
