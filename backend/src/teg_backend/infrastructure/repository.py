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
        "profile_id": row["profile_id"] if "profile_id" in row.keys() else None,
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
        "profile_id": player.get("profile_id"),
    }


def public_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Vista de perfil sin el hash del token."""
    return {
        "id": profile["id"],
        "nickname": profile["nickname"],
        "color": profile["color"],
        "avatar_asset_id": profile["avatar_asset_id"],
        "created_at": profile["created_at"],
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


async def list_games_by_status(db: Database, status: str) -> list[dict]:
    rows = await db.fetchall("SELECT * FROM games WHERE status = ?", (status,))
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
    profile_id: str | None = None,
) -> dict:
    player_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO players (id, game_id, nickname, role, color, token_hash,"
        " nickname_editable, profile_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (player_id, game_id, nickname, role, color, token_hash,
         int(nickname_editable), profile_id),
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
        "nickname_editable", "is_ready", "eliminated", "joined_at", "role",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    cols = ", ".join(f"{k} = ?" for k in updates)
    params = tuple(int(v) if isinstance(v, bool) else v for v in updates.values())
    await db.execute(f"UPDATE players SET {cols} WHERE id = ?", params + (player_id,))


# --- profiles ---------------------------------------------------------------

def _row_to_profile(row: aiosqlite.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "nickname": row["nickname"],
        "color": row["color"],
        "avatar_asset_id": row["avatar_asset_id"],
        "token_hash": row["token_hash"],
        "created_at": row["created_at"],
    }


async def create_profile(
    db: Database, nickname: str, token_hash: str, color: str | None = None
) -> dict:
    profile_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO profiles (id, nickname, color, token_hash) VALUES (?, ?, ?, ?)",
        (profile_id, nickname, color, token_hash),
    )
    row = await db.fetchone("SELECT * FROM profiles WHERE id = ?", (profile_id,))
    assert row is not None
    return _row_to_profile(row)


async def get_profile(db: Database, profile_id: str) -> dict | None:
    row = await db.fetchone("SELECT * FROM profiles WHERE id = ?", (profile_id,))
    return _row_to_profile(row) if row else None


async def find_profile_by_token_hash(db: Database, token_hash: str) -> dict | None:
    row = await db.fetchone("SELECT * FROM profiles WHERE token_hash = ?", (token_hash,))
    return _row_to_profile(row) if row else None


async def list_profiles(db: Database) -> list[dict]:
    rows = await db.fetchall("SELECT * FROM profiles ORDER BY created_at")
    return [_row_to_profile(r) for r in rows]


async def update_profile(db: Database, profile_id: str, **fields: Any) -> None:
    allowed = {"nickname", "color", "avatar_asset_id", "token_hash"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    cols = ", ".join(f"{k} = ?" for k in updates)
    await db.execute(
        f"UPDATE profiles SET {cols} WHERE id = ?",
        tuple(updates.values()) + (profile_id,),
    )


# --- events ----------------------------------------------------------------

async def next_sequence_number(db: Database, game_id: str) -> int:
    row = await db.fetchone(
        "SELECT COALESCE(MAX(sequence_number), 0) AS seq FROM events WHERE game_id = ?",
        (game_id,),
    )
    return int(row["seq"]) + 1 if row else 1


async def next_public_sequence(db: Database, game_id: str) -> int:
    row = await db.fetchone(
        "SELECT COALESCE(MAX(public_sequence), 0) AS seq FROM events WHERE game_id = ?",
        (game_id,),
    )
    return int(row["seq"]) + 1 if row else 1


async def append_event(db: Database, event: dict[str, Any]) -> None:
    await db.execute(
        "INSERT INTO events (id, game_id, sequence_number, public_sequence, event_type,"
        " actor_id, target_id, visibility, schema_version, payload_json, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            event["event_id"], event["game_id"], event["sequence_number"],
            event.get("public_sequence"),
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


# --- audios personalizados por perfil ---------------------------------------

def _row_to_profile_taunt(row: aiosqlite.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "owner_profile_id": row["owner_profile_id"],
        "target_profile_id": row["target_profile_id"],
        "event_type": row["event_type"],
        "filename": row["filename"],
        "created_at": row["created_at"],
    }


async def upsert_profile_taunt(
    db: Database, owner_id: str, target_id: str, event_type: str, filename: str
) -> dict:
    taunt_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO profile_taunts (id, owner_profile_id, target_profile_id,"
        " event_type, filename) VALUES (?, ?, ?, ?, ?)"
        " ON CONFLICT(owner_profile_id, target_profile_id, event_type)"
        " DO UPDATE SET filename = excluded.filename",
        (taunt_id, owner_id, target_id, event_type, filename),
    )
    row = await db.fetchone(
        "SELECT * FROM profile_taunts WHERE owner_profile_id = ?"
        " AND target_profile_id = ? AND event_type = ?",
        (owner_id, target_id, event_type),
    )
    assert row is not None
    return _row_to_profile_taunt(row)


async def find_profile_taunt(
    db: Database, owner_id: str, target_id: str, event_type: str
) -> dict | None:
    row = await db.fetchone(
        "SELECT * FROM profile_taunts WHERE owner_profile_id = ?"
        " AND target_profile_id = ? AND event_type = ?",
        (owner_id, target_id, event_type),
    )
    return _row_to_profile_taunt(row) if row else None


async def list_profile_taunts(db: Database, owner_id: str) -> list[dict]:
    rows = await db.fetchall(
        "SELECT * FROM profile_taunts WHERE owner_profile_id = ? ORDER BY created_at",
        (owner_id,),
    )
    return [_row_to_profile_taunt(r) for r in rows]


async def count_profile_taunts(db: Database, owner_id: str) -> int:
    row = await db.fetchone(
        "SELECT COUNT(*) AS n FROM profile_taunts WHERE owner_profile_id = ?", (owner_id,)
    )
    return int(row["n"]) if row else 0


async def delete_profile_taunt(db: Database, owner_id: str, taunt_id: str) -> str | None:
    row = await db.fetchone(
        "SELECT filename FROM profile_taunts WHERE id = ? AND owner_profile_id = ?",
        (taunt_id, owner_id),
    )
    if row is None:
        return None
    await db.execute("DELETE FROM profile_taunts WHERE id = ?", (taunt_id,))
    return row["filename"]


# --- estadísticas por partida ------------------------------------------------

async def save_game_stats(
    db: Database, game_id: str, player_id: str, profile_id: str | None,
    stats: dict, trophies: list[dict],
) -> None:
    await db.execute(
        "INSERT OR REPLACE INTO game_stats (game_id, player_id, profile_id,"
        " stats_json, trophies_json) VALUES (?, ?, ?, ?, ?)",
        (game_id, player_id, profile_id,
         json.dumps(stats, ensure_ascii=False), json.dumps(trophies, ensure_ascii=False)),
    )


async def get_game_stats(db: Database, game_id: str) -> list[dict]:
    rows = await db.fetchall("SELECT * FROM game_stats WHERE game_id = ?", (game_id,))
    return [
        {
            "game_id": r["game_id"],
            "player_id": r["player_id"],
            "profile_id": r["profile_id"],
            "stats": json.loads(r["stats_json"]),
            "trophies": json.loads(r["trophies_json"]),
        }
        for r in rows
    ]


async def get_profile_stats(db: Database, profile_id: str) -> dict:
    """Acumulado histórico de un perfil: suma de contadores + trofeos ganados."""
    rows = await db.fetchall(
        "SELECT stats_json, trophies_json FROM game_stats WHERE profile_id = ?",
        (profile_id,),
    )
    totals: dict = {}
    trophies: dict[str, int] = {}
    games = 0
    for r in rows:
        games += 1
        for k, v in json.loads(r["stats_json"]).items():
            if isinstance(v, bool):
                totals[k] = totals.get(k, 0) + (1 if v else 0)
            elif isinstance(v, (int, float)):
                totals[k] = totals.get(k, 0) + v
    for r in rows:
        for t in json.loads(r["trophies_json"]):
            trophies[t["title"]] = trophies.get(t["title"], 0) + 1
    return {"games_played": games, "totals": totals, "trophies": trophies}
