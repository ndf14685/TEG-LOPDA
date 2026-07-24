"""Acceso a datos. Todas las funciones reciben la Database y devuelven dicts."""

from __future__ import annotations

import json
import uuid
from typing import Any

import aiosqlite

from .db import Database


def _row_to_game(row: aiosqlite.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "code": row["code"],
        "name": row["name"],
        "status": row["status"],
        "config": json.loads(row["config_json"]),
        "state": json.loads(row["state_json"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _row_to_player(row: aiosqlite.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "game_id": row["game_id"],
        "nickname": row["nickname"],
        "role": row["role"],
        "color": row["color"],
        "avatar_asset_id": row["avatar_asset_id"],
        "token_hash": row["token_hash"],
        "token_revoked": bool(row["token_revoked"]),
        "nickname_editable": bool(row["nickname_editable"]),
        "is_ready": bool(row["is_ready"]),
        "eliminated": bool(row["eliminated"]),
        "joined_at": row["joined_at"],
        "created_at": row["created_at"],
    }


def public_game(game: dict[str, Any]) -> dict[str, Any]:
    """Vista pública de partida para snapshots y respuestas de join."""
    config = game.get("config", {})
    return {
        "id": game["id"],
        "code": game["code"],
        "name": game["name"],
        "status": game["status"],
        "game_mode": config.get("game_mode"),
        "map_assets": config.get("map_assets"),
    }


def public_player(player: dict[str, Any]) -> dict[str, Any]:
    """Vista de jugador sin datos sensibles (para snapshots y eventos)."""
    return {
        "id": player["id"],
        "nickname": player["nickname"],
        "role": player["role"],
        "color": player["color"],
        "avatar_asset_id": player["avatar_asset_id"],
        "is_ready": player["is_ready"],
        "eliminated": player["eliminated"],
        "joined": player["joined_at"] is not None,
    }


# --- games -----------------------------------------------------------------

async def create_game(db: Database, code: str, name: str, config: dict) -> dict:
    game_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO games (id, code, name, config_json) VALUES (?, ?, ?, ?)",
        (game_id, code, name, json.dumps(config)),
    )
    row = await db.fetchone("SELECT * FROM games WHERE id = ?", (game_id,))
    assert row is not None
    return _row_to_game(row)


async def get_game(db: Database, game_id: str) -> dict | None:
    row = await db.fetchone("SELECT * FROM games WHERE id = ?", (game_id,))
    return _row_to_game(row) if row else None


async def get_game_by_code(db: Database, code: str) -> dict | None:
    row = await db.fetchone("SELECT * FROM games WHERE code = ?", (code,))
    return _row_to_game(row) if row else None


async def list_games(db: Database) -> list[dict]:
    rows = await db.fetchall("SELECT * FROM games ORDER BY created_at DESC")
    return [_row_to_game(r) for r in rows]


async def update_game_status(db: Database, game_id: str, status: str) -> None:
    await db.execute(
        "UPDATE games SET status = ?, updated_at = datetime('now') WHERE id = ?",
        (status, game_id),
    )


async def update_game_state(db: Database, game_id: str, state: dict) -> None:
    await db.execute(
        "UPDATE games SET state_json = ?, updated_at = datetime('now') WHERE id = ?",
        (json.dumps(state), game_id),
    )


async def update_game_config(db: Database, game_id: str, config: dict) -> None:
    await db.execute(
        "UPDATE games SET config_json = ?, updated_at = datetime('now') WHERE id = ?",
        (json.dumps(config), game_id),
    )


# --- players ---------------------------------------------------------------

async def create_player(
    db: Database,
    game_id: str,
    nickname: str,
    role: str,
    token_hash: str | None,
    color: str | None = None,
    nickname_editable: bool = True,
) -> dict:
    player_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO players (id, game_id, nickname, role, color, token_hash,"
        " nickname_editable) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (player_id, game_id, nickname, role, color, token_hash, int(nickname_editable)),
    )
    row = await db.fetchone("SELECT * FROM players WHERE id = ?", (player_id,))
    assert row is not None
    return _row_to_player(row)


async def get_player(db: Database, player_id: str) -> dict | None:
    row = await db.fetchone("SELECT * FROM players WHERE id = ?", (player_id,))
    return _row_to_player(row) if row else None


async def get_players(db: Database, game_id: str) -> list[dict]:
    rows = await db.fetchall(
        "SELECT * FROM players WHERE game_id = ? ORDER BY created_at", (game_id,)
    )
    return [_row_to_player(r) for r in rows]


async def find_player_by_token_hash(db: Database, game_id: str, token_hash: str) -> dict | None:
    row = await db.fetchone(
        "SELECT * FROM players WHERE game_id = ? AND token_hash = ? AND token_revoked = 0",
        (game_id, token_hash),
    )
    return _row_to_player(row) if row else None


async def update_player(db: Database, player_id: str, **fields: Any) -> None:
    allowed = {
        "nickname", "color", "avatar_asset_id", "token_hash", "token_revoked",
        "nickname_editable", "is_ready", "eliminated", "joined_at",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    cols = ", ".join(f"{k} = ?" for k in updates)
    params = tuple(int(v) if isinstance(v, bool) else v for v in updates.values())
    await db.execute(f"UPDATE players SET {cols} WHERE id = ?", params + (player_id,))


# --- events ----------------------------------------------------------------

async def next_sequence_number(db: Database, game_id: str) -> int:
    row = await db.fetchone(
        "SELECT COALESCE(MAX(sequence_number), 0) AS seq FROM events WHERE game_id = ?",
        (game_id,),
    )
    return int(row["seq"]) + 1 if row else 1


async def append_event(db: Database, event: dict[str, Any]) -> None:
    await db.execute(
        "INSERT INTO events (id, game_id, sequence_number, event_type, actor_id,"
        " target_id, visibility, schema_version, payload_json, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            event["event_id"], event["game_id"], event["sequence_number"],
            event["event_type"], event["actor_id"], event["target_id"],
            event["visibility"], event["schema_version"],
            json.dumps(event["payload"]), event["timestamp"],
        ),
    )


async def get_events(
    db: Database,
    game_id: str,
    after: int = 0,
    limit: int = 500,
    public_only: bool = False,
) -> list[dict]:
    sql = (
        "SELECT * FROM events WHERE game_id = ? AND sequence_number > ?"
        + (" AND visibility = 'public'" if public_only else "")
        + " ORDER BY sequence_number LIMIT ?"
    )
    rows = await db.fetchall(sql, (game_id, after, limit))
    return [
        {
            "event_id": r["id"],
            "event_type": r["event_type"],
            "game_id": r["game_id"],
            "actor_id": r["actor_id"],
            "target_id": r["target_id"],
            "timestamp": r["created_at"],
            "sequence_number": r["sequence_number"],
            "payload": json.loads(r["payload_json"]),
            "visibility": r["visibility"],
            "schema_version": r["schema_version"],
            "persisted": True,
        }
        for r in rows
    ]


# --- taunts ----------------------------------------------------------------

async def upsert_taunt(
    db: Database, game_id: str, owner_id: str, target_id: str, event_type: str, asset_id: str
) -> dict:
    taunt_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO taunt_assets (id, game_id, owner_player_id, target_player_id,"
        " event_type, asset_id) VALUES (?, ?, ?, ?, ?, ?)"
        " ON CONFLICT(game_id, owner_player_id, target_player_id, event_type)"
        " DO UPDATE SET asset_id = excluded.asset_id",
        (taunt_id, game_id, owner_id, target_id, event_type, asset_id),
    )
    return {
        "game_id": game_id,
        "owner_player_id": owner_id,
        "target_player_id": target_id,
        "event_type": event_type,
        "asset_id": asset_id,
    }


async def find_taunt(
    db: Database, game_id: str, owner_id: str, target_id: str, event_type: str
) -> str | None:
    row = await db.fetchone(
        "SELECT asset_id FROM taunt_assets WHERE game_id = ? AND owner_player_id = ?"
        " AND target_player_id = ? AND event_type = ?",
        (game_id, owner_id, target_id, event_type),
    )
    return row["asset_id"] if row else None


# --- snapshots por turno (replay) ------------------------------------------

async def save_turn_snapshot(db: Database, game_id: str, turn_number: int, state: dict) -> None:
    await db.execute(
        "INSERT OR REPLACE INTO turn_snapshots (game_id, turn_number, state_json)"
        " VALUES (?, ?, ?)",
        (game_id, int(turn_number), json.dumps(state, ensure_ascii=False)),
    )


async def get_turn_snapshot(db: Database, game_id: str, turn_number: int) -> dict | None:
    row = await db.fetchone(
        "SELECT state_json FROM turn_snapshots WHERE game_id = ? AND turn_number = ?",
        (game_id, int(turn_number)),
    )
    return json.loads(row["state_json"]) if row else None


async def list_snapshot_turns(db: Database, game_id: str) -> list[int]:
    rows = await db.fetchall(
        "SELECT turn_number FROM turn_snapshots WHERE game_id = ? ORDER BY turn_number",
        (game_id,),
    )
    return [int(r["turn_number"]) for r in rows]
