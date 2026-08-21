from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints


UserName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=50,
    ),
]


MessageContent = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=2000,
    ),
]


Password = Annotated[
    str,
    StringConstraints(
        min_length=8,
        max_length=128,
    ),
]


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: UserName
    email: EmailStr
    password: Password


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: Password


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime


class CurrentUserResponse(UserResponse):
    email: EmailStr
    is_admin: bool


class AdminUserResponse(CurrentUserResponse):
    deleted_at: datetime | None


class DMRoomRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_user_id: int = Field(gt=0)


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class RoomDetailResponse(RoomResponse):
    other_user: UserResponse


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    sender_id: int
    content: str
    created_at: datetime


class MessageCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: MessageContent


class MessageCreatedEvent(BaseModel):
    type: Literal["message.created"] = "message.created"
    data: MessageResponse


