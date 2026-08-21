from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Message


def list_room_messages(
    db: Session,
    room_id: int,
) -> list[Message]:
    stmt = (
        select(Message)
        .where(Message.room_id == room_id)
        .order_by(Message.id.asc())
    )

    return list(db.scalars(stmt))


def create_message(
    db: Session,
    room_id: int,
    sender_id: int,
    content: str,
) -> Message:
    new_message = Message(
        room_id=room_id,
        sender_id=sender_id,
        content=content,
    )

    try:
        db.add(new_message)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

    db.refresh(new_message)

    return new_message