from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import (
    CurrentUserResponse,
    LoginRequest,
    RegisterRequest,
)
from app.security import (
    DUMMY_PASSWORD_HASH,
    clear_auth_cookie,
    create_access_token,
    hash_password,
    set_auth_cookie,
    verify_password,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    register_data: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> User:
    normalized_email = str(register_data.email).lower()
    duplicate_stmt = select(User).where(
        or_(
            User.username == register_data.username,
            User.email == normalized_email,
        )
    )

    if db.scalars(duplicate_stmt).one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already registered",
        )

    new_user = User(
        username=register_data.username,
        email=normalized_email,
        password_hash=hash_password(register_data.password),
    )

    try:
        db.add(new_user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already registered",
        ) from None

    db.refresh(new_user)
    token = create_access_token(new_user.id)
    set_auth_cookie(response, token)
    return new_user


@router.post("/login", response_model=CurrentUserResponse)
def login(
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> User:
    normalized_email = str(login_data.email).lower()
    stmt = select(User).where(User.email == normalized_email)
    user = db.scalars(stmt).one_or_none()

    if user is None or user.deleted_at is not None:
        # 存在しないメールでもハッシュ計算を行い、応答時間から登録有無を推測しにくくする。
        verify_password(login_data.password, DUMMY_PASSWORD_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user.id)
    set_auth_cookie(response, token)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    clear_auth_cookie(response)


@router.get("/me", response_model=CurrentUserResponse)
def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user
