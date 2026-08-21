from fastapi import (
    APIRouter,
    Depends,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from app.config import FRONTEND_ORIGINS
from app.database import SessionLocal
from app.models import RoomMember, User


router = APIRouter(tags=["websocket"])


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(
        self,
        room_id: int,
        websocket: WebSocket,
    ) -> None:
        await websocket.accept()

        connections = self.active_connections.setdefault(
            room_id,
            [],
        )
        connections.append(websocket)

    def disconnect(
        self,
        room_id: int,
        websocket: WebSocket,
    ) -> None:
        connections = self.active_connections.get(room_id)

        if connections is None:
            return

        if websocket in connections:
            connections.remove(websocket)

        if not connections:
            del self.active_connections[room_id]

    async def broadcast(
        self,
        room_id: int,
        event: dict[str, object],
    ) -> None:
        connections = list(
            self.active_connections.get(room_id, [])
        )
        disconnected_connections: list[WebSocket] = []

        for connection in connections:
            try:
                await connection.send_json(event)
            except (WebSocketDisconnect, RuntimeError):
                disconnected_connections.append(connection)

        for connection in disconnected_connections:
            self.disconnect(
                room_id=room_id,
                websocket=connection,
            )


manager = ConnectionManager()


def get_authorized_user_id(
    room_id: int,
    user_id: int = Query(gt=0),
) -> int | None:
    with SessionLocal() as db:
        current_user = db.get(User, user_id)
        room_member = db.get(
            RoomMember,
            (room_id, user_id),
        )

        if current_user is None or room_member is None:
            return None

        return user_id


@router.websocket("/ws/rooms/{room_id}")
async def room_websocket(
    websocket: WebSocket,
    room_id: int,
    authorized_user_id: int | None = Depends(
        get_authorized_user_id
    ),
) -> None:
    origin = websocket.headers.get("origin")
    is_allowed_origin = (
        origin is not None
        and origin.rstrip("/") in FRONTEND_ORIGINS
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
