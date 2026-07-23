from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from teg_backend.config import Settings
from teg_backend.main import create_app

ADMIN = {"X-Admin-Token": "test-admin"}


@pytest.fixture()
def client(tmp_path):
    settings = Settings(
        env="dev",
        db_path=str(tmp_path / "test.db"),
        admin_token="test-admin",
        commentator_cooldown_seconds=0.0,
        reconnect_grace_seconds=0.05,
        ai_player_think_seconds=0.01,
        public_base_url="http://testserver",
    )
    app = create_app(settings)
    with TestClient(app) as c:
        yield c


def create_game(client: TestClient, name: str = "partida-test", config: dict | None = None) -> dict:
    resp = client.post("/api/admin/games", json={"name": name, "config": config or {}}, headers=ADMIN)
    assert resp.status_code == 200, resp.text
    return resp.json()["game"]


def invite(client: TestClient, game_id: str, nickname: str, role: str = "player") -> dict:
    resp = client.post(
        f"/api/admin/games/{game_id}/players",
        json={"nickname": nickname, "role": role},
        headers=ADMIN,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def confirm_join(client: TestClient, code: str, token: str, nickname: str | None = None) -> dict:
    body = {"nickname": nickname} if nickname else {}
    resp = client.post(f"/api/join/{code}/{token}", json=body)
    assert resp.status_code == 200, resp.text
    return resp.json()


def recv_until(ws, event_type: str, max_msgs: int = 50) -> dict:
    """Lee mensajes hasta encontrar el tipo esperado (tolera intercalados)."""
    for _ in range(max_msgs):
        msg = ws.receive_json()
        if msg.get("event_type") == event_type:
            return msg
    raise AssertionError(f"no llegó el evento {event_type} en {max_msgs} mensajes")
