import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.models import User
from app.security import hash_password


TEST_PASSWORD = "correct-horse-battery"


def register(
    client: TestClient,
    username: str,
    email: str,
) -> dict[str, object]:
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": TEST_PASSWORD,
        },
    )
    assert response.status_code == 201
    return response.json()


def login(
    client: TestClient,
    email: str,
    password: str = TEST_PASSWORD,
) -> dict[str, object]:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()


def open_dm(
    client: TestClient,
    target_user: dict[str, object],
) -> dict[str, object]:
    response = client.post(
        "/api/rooms/dm",
        json={"target_user_id": target_user["id"]},
    )
    assert response.status_code == 200
    return response.json()


def test_registration_hashes_password_and_login_sets_http_only_cookie(
    client: TestClient,
    test_session_factory,
) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "username": "  Alice  ",
            "email": "Alice@Example.com",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 201
    assert response.json()["username"] == "Alice"
    assert response.json()["email"] == "alice@example.com"
    assert "password" not in response.json()
    assert "HttpOnly" in response.headers["set-cookie"]

    with test_session_factory() as db:
        saved_user = db.get(User, response.json()["id"])
        assert saved_user is not None
        assert saved_user.password_hash != TEST_PASSWORD

    client.cookies.clear()
    assert client.get("/api/auth/me").status_code == 401
    assert login(client, "ALICE@example.com")["id"] == response.json()["id"]

    wrong_password = client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "wrong-password"},
    )
    assert wrong_password.status_code == 401

    duplicate = client.post(
        "/api/auth/register",
        json={
            "username": "Alice2",
            "email": "alice@example.com",
            "password": TEST_PASSWORD,
        },
    )
    assert duplicate.status_code == 409


def test_user_list_requires_authentication_and_excludes_current_user(
    client: TestClient,
) -> None:
    alice = register(client, "Alice", "alice@example.com")
    bob = register(client, "Bob", "bob@example.com")

    client.cookies.clear()
    assert client.get("/api/users").status_code == 401

    login(client, "alice@example.com")
    response = client.get("/api/users")

    assert response.status_code == 200
    assert [user["id"] for user in response.json()] == [bob["id"]]
    assert alice["id"] not in [user["id"] for user in response.json()]


def test_dm_is_canonical_and_outsider_cannot_read_messages(
    client: TestClient,
) -> None:
    alice = register(client, "Alice", "alice@example.com")
    bob = register(client, "Bob", "bob@example.com")
    register(client, "Outsider", "outsider@example.com")

    login(client, "alice@example.com")
    alice_room = open_dm(client, bob)
    room_detail = client.get(f"/api/rooms/{alice_room['id']}")
    assert room_detail.status_code == 200
    assert room_detail.json()["other_user"]["username"] == "Bob"

    login(client, "bob@example.com")
    bob_room = open_dm(client, alice)
    assert alice_room["id"] == bob_room["id"]

    login(client, "outsider@example.com")
    assert client.get(f"/api/rooms/{alice_room['id']}").status_code == 403
    response = client.get(f"/api/rooms/{alice_room['id']}/messages")
    assert response.status_code == 403


def test_message_is_saved_and_broadcast_by_authenticated_websocket(
    client: TestClient,
) -> None:
    alice = register(client, "Alice", "alice@example.com")
    bob = register(client, "Bob", "bob@example.com")
    login(client, "alice@example.com")
    room = open_dm(client, bob)

    with client.websocket_connect(
        f"/ws/rooms/{room['id']}",
        headers={"origin": "http://localhost:3000"},
    ) as websocket:
        login(client, "bob@example.com")
        response = client.post(
            f"/api/rooms/{room['id']}/messages",
            json={"content": "  hello  "},
        )

        assert response.status_code == 201
        assert response.json()["content"] == "hello"

        event = websocket.receive_json()
        assert event["type"] == "message.created"
        assert event["data"]["id"] == response.json()["id"]
        assert event["data"]["sender_id"] == bob["id"]
        assert alice["id"] != bob["id"]


def test_websocket_rejects_untrusted_origin(client: TestClient) -> None:
    register(client, "Alice", "alice@example.com")
    bob = register(client, "Bob", "bob@example.com")
    login(client, "alice@example.com")
    room = open_dm(client, bob)

    with pytest.raises(WebSocketDisconnect) as error:
        with client.websocket_connect(
            f"/ws/rooms/{room['id']}",
            headers={"origin": "https://evil.example"},
        ) as websocket:
            websocket.receive_json()

    assert error.value.code == 1008


def test_only_admin_can_soft_delete_user(
    client: TestClient,
    test_session_factory,
) -> None:
    target = register(client, "Target", "target@example.com")

    with test_session_factory() as db:
        admin = User(
            username="Admin",
            email="admin@example.com",
            password_hash=hash_password(TEST_PASSWORD),
            is_admin=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        admin_id = admin.id

    assert client.get("/api/admin/users").status_code == 403

    login(client, "admin@example.com")
    delete_response = client.delete(f"/api/admin/users/{target['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted_at"] is not None
    assert client.delete(f"/api/admin/users/{admin_id}").status_code == 400

    visible_users = client.get("/api/users")
    assert visible_users.status_code == 200
    assert target["id"] not in [user["id"] for user in visible_users.json()]

    client.cookies.clear()
    deleted_login = client.post(
        "/api/auth/login",
        json={"email": "target@example.com", "password": TEST_PASSWORD},
    )
    assert deleted_login.status_code == 401
