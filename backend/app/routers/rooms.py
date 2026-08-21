from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import DMRoom, Room, RoomMember, User
from app.schemas import DMRoomRequest, RoomDetailResponse, RoomResponse
from app.services.rooms import get_or_create_dm_room


router = APIRouter(
    prefix="/api/rooms",
    tags=["rooms"],
)


@router.get("/{room_id}", response_model=RoomDetailResponse)
def read_dm_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoomDetailResponse:
    room = db.get(Room, room_id)
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    room_member = db.get(RoomMember, (room_id, current_user.id))
    if room_member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room",
        )

    dm_room = db.get(DMRoom, room_id)
    if dm_room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DM room not found",
        )

    # canonical pairのうち、現在ユーザーではない側が画面に出す相手になる。
    other_user_id = (
        dm_room.user_high_id
        if dm_room.user_low_id == current_user.id
        else dm_room.user_low_id
    )
    other_user = db.get(User, other_user_id)
    if other_user is None:
        raise RuntimeError("DM room references a user that does not exist")

    return RoomDetailResponse(
        id=room.id,
        created_at=room.created_at,
        other_user=other_user,
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

    if target_user is None or target_user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found",
        )

    return get_or_create_dm_room(
        db=db,
        current_user_id=current_user.id,
        target_user_id=target_user.id,
    )
