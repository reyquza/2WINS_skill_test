import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


def login(client: TestClient, username: str) -> dict[str, object]:
    response = client.post("/api/login", json={"username": username})
    assert response.status_code == 200
    return response.json()


def user_headers(user: dict[str, object]) -> dict[str, str]:
    return {"X-User-Id": str(user["id"])}


def open_dm(
    client: TestClient,
    current_user: dict[str, object],
    target_user: dict[str, object],
) -> dict[str, object]:
    response = client.post(
        "/api/rooms/dm",
        headers=user_headers(current_user),
        json={"target_user_id": target_user["id"]},
    )
    assert response.status_code == 200
    return response.json()


def test_login_trims_username_and_reuses_existing_user(client: TestClient) -> None:
    first_login = login(client, "  Alice  ")
    second_login = login(client, "Alice")

    assert first_login["username"] == "Alice"
    assert second_login["id"] == first_login["id"]

    invalid_response = client.post(
        "/api/login",
        json={"username": "Alice", "unexpected": True},
    )
    assert invalid_response.status_code == 422


def test_user_list_requires_login_and_excludes_current_user(
    client: TestClient,
) -> None:
    alice = login(client, "Alice")
    bob = login(client, "Bob")

    assert client.get("/api/users").status_code == 401

    response = client.get("/api/users", headers=user_headers(alice))

    assert response.status_code == 200
    assert [user["id"] for user in response.json()] == [bob["id"]]


def test_dm_is_canonical_and_outsider_cannot_read_messages(
    client: TestClient,
) -> None:
    alice = login(client, "Alice")
    bob = login(client, "Bob")
    outsider = login(client, "Outsider")

    alice_room = open_dm(client, alice, bob)
    bob_room = open_dm(client, bob, alice)

    assert alice_room["id"] == bob_room["id"]

    response = client.get(
        f"/api/rooms/{alice_room['id']}/messages",
        headers=user_headers(outsider),
    )
    assert response.status_code == 403


def test_message_is_saved_and_broadcast_by_websocket(client: TestClient) -> None:
    alice = login(client, "Alice")
    bob = login(client, "Bob")
    room = open_dm(client, alice, bob)
    websocket_url = f"/ws/rooms/{room['id']}?user_id={alice['id']}"

    with client.websocket_connect(
        websocket_url,
        headers={"origin": "http://localhost:3000"},
    ) as websocket:
        response = client.post(
            f"/api/rooms/{room['id']}/messages",
            headers=user_headers(bob),
            json={"content": "  hello  "},
        )

        assert response.status_code == 201
        assert response.json()["content"] == "hello"

        event = websocket.receive_json()
        assert event["type"] == "message.created"
        assert event["data"]["id"] == response.json()["id"]


def test_websocket_rejects_untrusted_origin(client: TestClient) -> None:
    alice = login(client, "Alice")
    bob = login(client, "Bob")
    room = open_dm(client, alice, bob)

    with pytest.raises(WebSocketDisconnect) as error:
        with client.websocket_connect(
            f"/ws/rooms/{room['id']}?user_id={alice['id']}",
            headers={"origin": "https://evil.example"},
        ) as websocket:
            websocket.receive_json()

    assert error.value.code == 1008
