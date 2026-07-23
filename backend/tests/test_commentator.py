"""El comentarista mock comenta eventos sin bloquear el juego."""

import time

import pytest

from conftest import ADMIN, confirm_join, create_game, invite
from teg_backend.ai.commentator import Comment, CommentRequest, MockCommentator


@pytest.fixture()
def anyio_backend():
    return "asyncio"


def _request(event_type: str, humor: int, payload: dict | None = None) -> CommentRequest:
    return CommentRequest(
        game_id="g1",
        event={
            "event_type": event_type, "actor_id": "p1", "target_id": "p2",
            "payload": payload or {},
        },
        recent_events=[],
        players=[
            {"id": "p1", "nickname": "Nessi", "role": "player"},
            {"id": "p2", "nickname": "Daro", "role": "player"},
        ],
        humor_level=humor,
    )


@pytest.mark.anyio
async def test_mock_commentator_levels_and_rotation():
    mock = MockCommentator()
    assert await mock.generate(_request("game.started", 0)) is None  # apagado

    c1 = await mock.generate(_request("attack.resolved", 3, {"attacker_losses": 2, "defender_losses": 1}))
    c2 = await mock.generate(_request("attack.resolved", 3, {"attacker_losses": 2, "defender_losses": 1}))
    assert isinstance(c1, Comment) and isinstance(c2, Comment)
    assert "Nessi" in c1.text or "Daro" in c1.text
    assert c1.text != c2.text  # rotación de plantillas


@pytest.mark.anyio
async def test_mock_commentator_remembers_bad_streaks():
    mock = MockCommentator()
    await mock.generate(_request("dice.rolled", 3, {"dice": [1, 1, 2]}))
    c = await mock.generate(_request("dice.rolled", 3, {"dice": [2, 1, 1]}))
    assert c is not None
    assert "seguidas" in c.text  # recuerda la racha


def test_comment_emitted_in_game(client):
    """Integración: al arrancar la partida llega ai.comment.generated."""
    game = create_game(client)  # comentarista habilitado, cooldown 0 en tests
    inv1 = invite(client, game["id"], "Nessi")
    inv2 = invite(client, game["id"], "Daro")
    confirm_join(client, game["code"], inv1["token"])
    confirm_join(client, game["code"], inv2["token"])
    resp = client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
    assert resp.status_code == 200

    deadline = time.time() + 5
    comments = []
    while time.time() < deadline and not comments:
        resp = client.get(f"/api/admin/games/{game['id']}/events", headers=ADMIN)
        comments = [
            e for e in resp.json()["events"] if e["event_type"] == "ai.comment.generated"
        ]
        if not comments:
            time.sleep(0.1)
    assert comments, "el comentarista no comentó nada"
    assert 0 < len(comments[0]["payload"]["text"]) <= 280


def test_commentator_can_be_disabled_per_game(client):
    game = create_game(client, config={"commentator_enabled": False})
    inv1 = invite(client, game["id"], "A")
    inv2 = invite(client, game["id"], "B")
    confirm_join(client, game["code"], inv1["token"])
    confirm_join(client, game["code"], inv2["token"])
    client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
    time.sleep(0.5)
    resp = client.get(f"/api/admin/games/{game['id']}/events", headers=ADMIN)
    types = [e["event_type"] for e in resp.json()["events"]]
    assert "ai.comment.generated" not in types


def test_humor_level_capped(client):
    game = create_game(client, config={"humor_level": 4})
    # el nivel 4 está deshabilitado por defecto (humor_level_max=3)
    assert game["config"]["humor_level"] == 3
