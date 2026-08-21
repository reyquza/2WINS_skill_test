import os
from pathlib import Path


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "chat.db"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DEFAULT_DB_PATH.as_posix()}",
)

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "development-only-change-this-secret-before-deployment",
)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)
AUTH_COOKIE_NAME = "access_token"
AUTH_COOKIE_SECURE = (
    os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"
)

if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
    raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")


def _load_frontend_origins() -> tuple[str, ...]:
    raw_origins = os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:3000",
    )
    origins = tuple(
        origin.strip().rstrip("/")
        for origin in raw_origins.split(",")
        if origin.strip()
    )

    if not origins:
        raise RuntimeError("FRONTEND_ORIGINS must contain at least one origin")

    return origins


FRONTEND_ORIGINS = _load_frontend_origins()
