"""Snapshots por turno: base del replay (Etapa 8)."""

import pytest

from teg_backend.infrastructure import repository as repo
from teg_backend.infrastructure.db import Database


@pytest.fixture()
def anyio_backend():
    return "asyncio"


@pytest.fixture()
async def db(tmp_path):
    database = Database(str(tmp_path / "t.db"))
    await database.connect()
    yield database
    await database.close()


@pytest.mark.anyio
async def test_save_and_get_turn_snapshot(db):
    game = await repo.create_game(db, "ABC123", "test", {})
    state = {"turn": {"turn_number": 1}, "territories": {}}
    await repo.save_turn_snapshot(db, game["id"], 1, state)
    await repo.save_turn_snapshot(db, game["id"], 1, {"turn": {"turn_number": 1}, "x": 2})
    await repo.save_turn_snapshot(db, game["id"], 2, state)
    got = await repo.get_turn_snapshot(db, game["id"], 1)
    assert got is not None and got["x"] == 2
    assert await repo.get_turn_snapshot(db, game["id"], 99) is None
    assert await repo.list_snapshot_turns(db, game["id"]) == [1, 2]
