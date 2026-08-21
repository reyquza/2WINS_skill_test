import os
from pathlib import Path


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "chat.db"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DEFAULT_DB_PATH.as_posix()}",
)


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
