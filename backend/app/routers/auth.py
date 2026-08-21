from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.schemas import LoginRequest, UserResponse
from app.models import User


router = APIRouter(
    prefix="/api",
    tags=["auth"]
)

@router.post("/login", response_model=UserResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    stmt = select(User).where(User.username == login_data.username)
    user = db.scalars(stmt).one_or_none()
    
    if user is None:
        new_user = User(username=login_data.username)

        try:
            db.add(new_user)
            db.commit()
        except IntegrityError:
            db.rollback()

            # 同じユーザー名の同時登録が先に成功した場合は、そのユーザーを返す。
            user = db.scalars(stmt).one_or_none()
            if user is not None:
                return user

            raise

        db.refresh(new_user)
        
        return new_user

    return user
