from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

import app.websocket as websocket_module
from app.database import Base, get_db
from app.main import app


@pytest.fixture
def test_session_factory(tmp_path):
    database_path = tmp_path / "test.db"
    test_engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(test_engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(test_engine)
    factory = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )

    yield factory

    test_engine.dispose()


@pytest.fixture
def client(test_session_factory, monkeypatch) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(
        websocket_module,
        "SessionLocal",
        test_session_factory,
    )
    websocket_module.manager.active_connections.clear()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    websocket_module.manager.active_connections.clear()
