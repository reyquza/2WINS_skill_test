from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import DMRoom, Room, RoomMember


def get_or_create_dm_room(
    db: Session,
    current_user_id: int,
    target_user_id: int,
) -> Room:
    user_low_id, user_high_id = sorted(
        (current_user_id, target_user_id)
    )

    stmt = select(DMRoom).where(
        DMRoom.user_low_id == user_low_id,
        DMRoom.user_high_id == user_high_id,
    )

    dm_room = db.scalars(stmt).one_or_none()

    if dm_room is not None:
        existing_room = db.get(Room, dm_room.room_id)

        if existing_room is None:
            raise RuntimeError(
                "DMRoom references a Room that does not exist"
            )

        return existing_room

    new_room = Room()

    try:
        db.add(new_room)
        db.flush()

        current_member = RoomMember(
            room_id=new_room.id,
            user_id=current_user_id,
        )

        target_member = RoomMember(
            room_id=new_room.id,
            user_id=target_user_id,
        )

        new_dm_room = DMRoom(
            room_id=new_room.id,
            user_low_id=user_low_id,
            user_high_id=user_high_id,
        )

        db.add_all([
            current_member,
            target_member,
            new_dm_room,
        ])

        db.commit()
    except IntegrityError:
        db.rollback()

        # If both users open the same DM concurrently, reuse the room committed first.
        concurrent_dm_room = db.scalars(stmt).one_or_none()
        if concurrent_dm_room is not None:
            concurrent_room = db.get(Room, concurrent_dm_room.room_id)
            if concurrent_room is not None:
                return concurrent_room

        raise
    except SQLAlchemyError:
        db.rollback()
        raise

    db.refresh(new_room)

    return new_room
