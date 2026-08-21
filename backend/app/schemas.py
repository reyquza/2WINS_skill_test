from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


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


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: UserName


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime


class DMRoomRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_user_id: int = Field(gt=0)


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


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


