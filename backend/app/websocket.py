from dataclasses import dataclass

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.config import AUTH_COOKIE_NAME, FRONTEND_ORIGINS
from app.database import SessionLocal
from app.models import RoomMember, User
from app.security import decode_access_token


router = APIRouter(tags=["websocket"])


@dataclass
class ActiveConnection:
    user_id: int
    websocket: WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[
            int,
            list[ActiveConnection],
        ] = {}

    async def connect(
        self,
        room_id: int,
        user_id: int,
        websocket: WebSocket,
    ) -> None:
        await websocket.accept()
        connections = self.active_connections.setdefault(room_id, [])
        connections.append(
            ActiveConnection(
                user_id=user_id,
                websocket=websocket,
            )
        )

    def disconnect(
        self,
        room_id: int,
        websocket: WebSocket,
    ) -> None:
        connections = self.active_connections.get(room_id)
        if connections is None:
            return

        remaining_connections = [
            connection
            for connection in connections
            if connection.websocket is not websocket
        ]

        if remaining_connections:
            self.active_connections[room_id] = remaining_connections
        else:
            self.active_connections.pop(room_id, None)

    async def broadcast(
        self,
        room_id: int,
        event: dict[str, object],
    ) -> None:
        connections = list(self.active_connections.get(room_id, []))

        for connection in connections:
            try:
                await connection.websocket.send_json(event)
            except (WebSocketDisconnect, RuntimeError):
                self.disconnect(
                    room_id=room_id,
                    websocket=connection.websocket,
                )

    async def disconnect_user(self, user_id: int) -> None:
        matching_connections = [
            (room_id, connection)
            for room_id, connections in list(
                self.active_connections.items()
            )
            for connection in list(connections)
            if connection.user_id == user_id
        ]

        for room_id, connection in matching_connections:
            try:
                await connection.websocket.close(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="This account is no longer active",
                )
            except RuntimeError:
                pass
            finally:
                self.disconnect(
                    room_id=room_id,
                    websocket=connection.websocket,
                )


manager = ConnectionManager()


def get_authorized_user_id(
    room_id: int,
    token: str | None,
) -> int | None:
    if token is None:
        return None

    user_id = decode_access_token(token)
    if user_id is None:
        return None

    with SessionLocal() as db:
        current_user = db.get(User, user_id)
        room_member = db.get(RoomMember, (room_id, user_id))

        if (
            current_user is None
            or current_user.deleted_at is not None
            or room_member is None
        ):
            return None

        return user_id


@router.websocket("/ws/rooms/{room_id}")
async def room_websocket(
    websocket: WebSocket,
    room_id: int,
) -> None:
    origin = websocket.headers.get("origin")
    is_allowed_origin = (
        origin is not None
        and origin.rstrip("/") in FRONTEND_ORIGINS
    )
    authorized_user_id = get_authorized_user_id(
        room_id=room_id,
        token=websocket.cookies.get(AUTH_COOKIE_NAME),
    )

    if authorized_user_id is None or not is_allowed_origin:
        await websocket.accept()
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="WebSocket connection is not allowed",
        )
        return

    await manager.connect(
        room_id=room_id,
        user_id=authorized_user_id,
        websocket=websocket,
    )

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(
            room_id=room_id,
            websocket=websocket,
        )
