"""SQLite asíncrono con migraciones SQL versionadas (backend/migrations/*.sql)."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import aiosqlite

log = logging.getLogger("teg.db")

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "migrations"


class Database:
    def __init__(self, path: str) -> None:
        self.path = path
        self._conn: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("DB no conectada")
        return self._conn

    async def connect(self) -> None:
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        # NORMAL es seguro bajo WAL y saca un fsync de cada commit: con 8
        # jugadores son ~320-400 commits por ronda sobre un disco compartido
        await self._conn.execute("PRAGMA synchronous=NORMAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await self._conn.execute("PRAGMA busy_timeout=5000")
        await self.migrate()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def migrate(self) -> None:
        await self.conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            " version TEXT PRIMARY KEY,"
            " applied_at TEXT NOT NULL DEFAULT (datetime('now')))"
        )
        await self.conn.commit()
        cur = await self.conn.execute("SELECT version FROM schema_migrations")
        applied = {row["version"] for row in await cur.fetchall()}
        for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            version = sql_file.stem
            if version in applied:
                continue
            log.info("aplicando migración", extra={"ctx": {"version": version}})
            await self.conn.executescript(sql_file.read_text(encoding="utf-8"))
            await self.conn.execute(
                "INSERT INTO schema_migrations (version) VALUES (?)", (version,)
            )
            await self.conn.commit()

    async def execute(self, sql: str, params: tuple = ()) -> None:
        async with self._lock:
            await self.conn.execute(sql, params)
            await self.conn.commit()

    async def fetchone(self, sql: str, params: tuple = ()) -> aiosqlite.Row | None:
        async with self._lock:
            cur = await self.conn.execute(sql, params)
            return await cur.fetchone()

    async def fetchall(self, sql: str, params: tuple = ()) -> list[aiosqlite.Row]:
        async with self._lock:
            cur = await self.conn.execute(sql, params)
            return list(await cur.fetchall())
