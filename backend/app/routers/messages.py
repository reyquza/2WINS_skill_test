from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Room, RoomMember, User
from app.schemas import (
    MessageCreatedEvent,
    MessageCreateRequest,
    MessageResponse,
)
from app.services.messages import create_message, list_room_messages
from app.websocket import manager


router = APIRouter(
    prefix="/api/rooms",
    tags=["messages"],
)


def _require_room_access(
    db: Session,
    room_id: int,
    user_id: int,
) -> None:
    room = db.get(Room, room_id)

    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    room_member = db.get(
        RoomMember,
        (room_id, user_id),
    )

    if room_member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room",
        )


@router.get(
    "/{room_id}/messages",
    response_model=list[MessageResponse],
)
def read_room_messages(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_room_access(
        db=db,
        room_id=room_id,
        user_id=current_user.id,
    )

    return list_room_messages(
        db=db,
        room_id=room_id,
    )


@router.post(
    "/{room_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_room_message(
    room_id: int,
    message_request: MessageCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_room_access(
        db=db,
        room_id=room_id,
        user_id=current_user.id,
    )

    created_message = create_message(
        db=db,
        room_id=room_id,
        sender_id=current_user.id,
        content=message_request.content,
    )

    message_response = MessageResponse.model_validate(
        created_message
    )
    event = MessageCreatedEvent(data=message_response)

    background_tasks.add_task(
        manager.broadcast,
        room_id,
        event.model_dump(mode="json"),
    )

    return created_message
