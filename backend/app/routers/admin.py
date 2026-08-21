from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models import User
from app.schemas import AdminUserResponse
from app.websocket import manager


router = APIRouter(
    prefix="/api/admin/users",
    tags=["admin"],
)


@router.get("", response_model=list[AdminUserResponse])
def list_all_users(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[User]:
    stmt = select(User).order_by(User.created_at, User.id)
    return list(db.scalars(stmt).all())


@router.delete("/{user_id}", response_model=AdminUserResponse)
def soft_delete_user(
    user_id: int,
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot delete their own account",
        )

    target_user = db.get(User, user_id)
    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if target_user.deleted_at is None:
        target_user.deleted_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(target_user)
        background_tasks.add_task(
            manager.disconnect_user,
            target_user.id,
        )

    return target_user
