from fastapi import Header, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


def get_current_user(
    user_id: int | None = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db)
) -> User:
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-Id header missing"
        )
        
    current_user = db.get(User, user_id)
    
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
        
    return current_user