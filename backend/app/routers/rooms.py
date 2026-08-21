from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import DMRoomRequest, RoomResponse
from app.services.rooms import get_or_create_dm_room


router = APIRouter(
    prefix="/api/rooms",
    tags=["rooms"],
)


@router.post("/dm", response_model=RoomResponse)
def open_dm_room(
    dm_request: DMRoomRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_user_id = dm_request.target_user_id

    if target_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create a DM room with yourself",
        )

    target_user = db.get(User, target_user_id)

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found",
        )

    return get_or_create_dm_room(
        db=db,
        current_user_id=current_user.id,
        target_user_id=target_user.id,
    )