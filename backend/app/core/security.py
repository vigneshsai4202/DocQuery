from fastapi import Depends
from sqlalchemy.orm import Session
import bcrypt

from app.db.base import get_db
from app.models.orm import User

_SYSTEM_USER_EMAIL = "app@docuquery.local"


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def get_current_user_id(db: Session = Depends(get_db)) -> str:
    """Returns a fixed single-user ID, creating the user on first call."""
    user = db.query(User).filter(User.email == _SYSTEM_USER_EMAIL).first()
    if not user:
        user = User(email=_SYSTEM_USER_EMAIL, hashed_password=hash_password("unused"))
        db.add(user)
        db.commit()
        db.refresh(user)
    return user.id
