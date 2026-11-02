from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import websocket
from app.config import FRONTEND_ORIGINS
from app.routers import admin, auth, messages, rooms, users


app = FastAPI(
    title="Relay API",
    description="API for secure one-to-one messaging with real-time updates",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(FRONTEND_ORIGINS),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(rooms.router)
app.include_router(messages.router)
app.include_router(admin.router)
app.include_router(websocket.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Relay API is running"}
