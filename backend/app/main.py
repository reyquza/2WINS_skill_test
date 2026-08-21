from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import websocket
from app.config import FRONTEND_ORIGINS
from app.routers import auth, messages, rooms, users


app = FastAPI(
    title="2WINS Chat API",
    description="1対1のリアルタイムチャットAPI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(FRONTEND_ORIGINS),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-User-Id"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(rooms.router)
app.include_router(messages.router)
app.include_router(websocket.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "2WINS Chat API is running"}
