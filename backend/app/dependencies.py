from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import AUTH_COOKIE_NAME
from app.database import get_db
from app.models import User
from app.security import decode_access_token


def _authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )


def get_current_user(
    access_token: str | None = Cookie(
        default=None,
        alias=AUTH_COOKIE_NAME,
    ),
    db: Session = Depends(get_db),
) -> User:
    if access_token is None:
        raise _authentication_error()

    user_id = decode_access_token(access_token)
    if user_id is None:
        raise _authentication_error()

    current_user = db.get(User, user_id)
    if current_user is None or current_user.deleted_at is not None:
        raise _authentication_error()

    return current_user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges are required",
        )

    return current_user
