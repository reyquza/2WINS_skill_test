from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.schemas import UserResponse
from app.models import User
from app.dependencies import get_current_user


router = APIRouter(
    prefix="/api/users",
    tags=["users"]
)

@router.get("", response_model=list[UserResponse])
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(User)
        .where(
            User.id != current_user.id,
            User.deleted_at.is_(None),
        )
        .order_by(User.username, User.id)
    )
    return db.scalars(stmt).all()
