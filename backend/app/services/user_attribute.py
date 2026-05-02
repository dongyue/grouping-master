from sqlalchemy.orm import Session
from app.models.user_attribute import UserAttribute


def sync_user_attributes(db: Session, user_id: int, attribute_values: dict[str, str]):
    for name, value in attribute_values.items():
        existing = db.query(UserAttribute).filter(
            UserAttribute.user_id == user_id,
            UserAttribute.attribute_name == name,
        ).first()
        if existing:
            existing.attribute_value = value
        else:
            db.add(UserAttribute(user_id=user_id, attribute_name=name, attribute_value=value))
