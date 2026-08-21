from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.current_timestamp(),
        nullable=False,
    )


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.current_timestamp(),
        nullable=False,
    )


class RoomMember(Base):
    __tablename__ = "room_members"

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"),
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        primary_key=True,
    )


class DMRoom(Base):
    __tablename__ = "dm_rooms"

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"),
        primary_key=True,
    )

    user_low_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    user_high_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_low_id",
            "user_high_id",
            name="uq_dm_rooms_user_pair",
        ),
        CheckConstraint(
            "user_low_id < user_high_id",
            name="ck_dm_rooms_user_order",
        ),
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
    )

    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.current_timestamp(),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_messages_room_id_id",
            "room_id",
            "id",
        ),
    )