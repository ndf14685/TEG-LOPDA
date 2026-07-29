from __future__ import annotations

import base64
import csv
import hashlib
import json
import re
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from ..config import Settings
from ..infrastructure.db import Database

SECRET_RE = re.compile(r"(?i)(token|secret|password|admin)[=:][^&\s]+")
JOIN_RE = re.compile(r"(/join/[^/]+/)[^/?#\s]+")
WS_RE = re.compile(r"(/ws/[^?]+\?token=)[^&#\s]+")


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def redact(value: Any) -> Any:
    if isinstance(value, str):
        text = JOIN_RE.sub(r"\1***", value)
        text = WS_RE.sub(r"\1***", text)
        return SECRET_RE.sub(lambda m: f"{m.group(1)}=***", text)
    if isinstance(value, list):
        return [redact(v) for v in value[:100]]
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for k, v in value.items():
            if any(s in k.lower() for s in ("token", "secret", "password")):
                clean[k] = "***"
            elif k in {"your_objective", "secretObjective", "secret_objective"}:
                clean[k] = "[redacted-secret-objective]"
            else:
                clean[k] = redact(v)
        return clean
    return value


def normalize_message(message: str) -> str:
    text = redact(message or "")
    text = re.sub(r"[0-9a-f]{8,}", "<hex>", str(text), flags=re.I)
    text = re.sub(r"\b\d+\b", "<n>", text)
    return text[:500]


def fingerprint_for(payload: dict[str, Any]) -> str:
    parts = [
        payload.get("category"),
        payload.get("error_type"),
        normalize_message(str(payload.get("message", ""))),
        payload.get("component") or payload.get("endpoint"),
        payload.get("phase"),
        payload.get("action"),
        payload.get("code"),
    ]
    raw = "|".join(str(p or "") for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def suggested_severity(payload: dict[str, Any]) -> str:
    category = str(payload.get("category") or "")
    msg = str(payload.get("message") or "").lower()
    code = str(payload.get("code") or "").lower()
    if category in {"desynchronization"} or "identity" in msg or "estado" in msg and "perd" in msg:
        return "CRITICAL"
    if "out of turn" in msg or "fuera de turno" in msg or "invalid_state" in code:
        return "MAJOR"
    if category in {"connection-problem"}:
        return "MAJOR"
    if category in {"visual-problem"}:
        return "MINOR"
    if category in {"incorrect-result"}:
        return "CRITICAL"
    if category in {"action-did-not-work"}:
        return "MAJOR"
    return "MINOR"


class PlaytestService:
    def __init__(self, db: Database, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.attach_dir = Path(settings.playtest_attachment_dir)

    @property
    def active(self) -> bool:
        if not self.settings.playtest_mode:
            return False
        if not self.settings.playtest_until:
            return True
        try:
            until = datetime.fromisoformat(self.settings.playtest_until)
            return datetime.now(until.tzinfo or UTC) <= until
        except ValueError:
            return True

    async def init(self) -> None:
        await self.db.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS playtest_sessions (
              id TEXT PRIMARY KEY, session_id TEXT UNIQUE NOT NULL, game_id TEXT,
              player_id TEXT, player_alias TEXT, build_version TEXT, user_agent TEXT,
              viewport_json TEXT, created_at TEXT NOT NULL, last_seen_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS playtest_incidents (
              id TEXT PRIMARY KEY, code TEXT UNIQUE NOT NULL, title TEXT NOT NULL,
              category TEXT NOT NULL, severity TEXT NOT NULL, status TEXT NOT NULL,
              fingerprint TEXT UNIQUE NOT NULL, frequency INTEGER NOT NULL DEFAULT 0,
              players_json TEXT NOT NULL DEFAULT '[]', games_json TEXT NOT NULL DEFAULT '[]',
              first_seen_at TEXT NOT NULL, last_seen_at TEXT NOT NULL,
              first_build TEXT, last_build TEXT, evidence_json TEXT NOT NULL DEFAULT '{}',
              steps_json TEXT NOT NULL DEFAULT '[]', workaround TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS playtest_occurrences (
              id TEXT PRIMARY KEY, incident_id TEXT NOT NULL, session_id TEXT, game_id TEXT,
              player_id TEXT, player_alias TEXT, request_id TEXT, event_id TEXT,
              sequence_number INTEGER, build_version TEXT, timestamp_utc TEXT NOT NULL,
              timestamp_local TEXT, payload_json TEXT NOT NULL,
              FOREIGN KEY(incident_id) REFERENCES playtest_incidents(id)
            );
            CREATE TABLE IF NOT EXISTS playtest_action_trail (
              id TEXT PRIMARY KEY, session_id TEXT NOT NULL, game_id TEXT, player_id TEXT,
              action_type TEXT NOT NULL, event_id TEXT, sequence_number INTEGER,
              timestamp_utc TEXT NOT NULL, data_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS playtest_attachments (
              id TEXT PRIMARY KEY, incident_id TEXT NOT NULL, occurrence_id TEXT,
              filename TEXT NOT NULL, mime TEXT NOT NULL, size_bytes INTEGER NOT NULL,
              path TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS playtest_status_changes (
              id TEXT PRIMARY KEY, incident_id TEXT NOT NULL, status_from TEXT,
              status_to TEXT, severity_from TEXT, severity_to TEXT, note TEXT,
              created_at TEXT NOT NULL
            );
            """
        )
        await self.db.conn.commit()
        self.attach_dir.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict[str, Any]:
        return {
            "active": self.active,
            "mode": self.settings.playtest_mode,
            "until": self.settings.playtest_until,
            "build": self.settings.playtest_build or "unknown",
            "env": self.settings.env,
            "retention_days": self.settings.playtest_retention_days,
            "server_time_utc": utc_now(),
        }

    async def register_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        sid = str(payload.get("session_id") or uuid.uuid4())
        now = utc_now()
        await self.db.execute(
            """
            INSERT INTO playtest_sessions
              (id, session_id, game_id, player_id, player_alias, build_version, user_agent, viewport_json, created_at, last_seen_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
              game_id=excluded.game_id, player_id=excluded.player_id, player_alias=excluded.player_alias,
              build_version=excluded.build_version, user_agent=excluded.user_agent,
              viewport_json=excluded.viewport_json, last_seen_at=excluded.last_seen_at
            """,
            (
                str(uuid.uuid4()), sid, payload.get("game_id"), payload.get("player_id"),
                str(payload.get("player_alias") or "")[:80],
                str(payload.get("build_version") or self.settings.playtest_build or "unknown")[:120],
                str(payload.get("user_agent") or "")[:500],
                json.dumps(redact(payload.get("viewport") or {})),
                now, now,
            ),
        )
        return {"session_id": sid, "active": self.active}

    async def add_action(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.active:
            return {"ok": True, "active": False}
        sid = str(payload.get("session_id") or "")
        now = utc_now()
        await self.db.execute(
            """
            INSERT INTO playtest_action_trail
              (id, session_id, game_id, player_id, action_type, event_id, sequence_number, timestamp_utc, data_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()), sid, payload.get("game_id"), payload.get("player_id"),
                str(payload.get("action_type") or "unknown")[:120], payload.get("event_id"),
                payload.get("sequence_number"), now,
                json.dumps(redact(payload.get("data") or {}), ensure_ascii=False),
            ),
        )
        rows = await self.db.fetchall(
            "SELECT id FROM playtest_action_trail WHERE session_id=? ORDER BY timestamp_utc DESC LIMIT -1 OFFSET 50",
            (sid,),
        )
        for row in rows:
            await self.db.execute("DELETE FROM playtest_action_trail WHERE id=?", (row["id"],))
        return {"ok": True}

    async def create_occurrence(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.active:
            return {"ok": True, "active": False}
        # Throttle por sesion (o, a falta de session_id, por partida o un
        # bucket compartido "sin-sesion" para que no haya un camino sin
        # freno) para CUALQUIER tipo. Antes solo miraba manual-report, y
        # los automaticos (pending-action-timeout, sequence-gap) entraban
        # sin freno: 41 ocurrencias en una partida. Contadores
        # independientes: manual-report no debe competir por cupo con los
        # automaticos ni viceversa.
        sid = str(payload.get("session_id") or "").strip()
        game_id_raw = str(payload.get("game_id") or "").strip()
        bucket = sid or game_id_raw or "sin-sesion"
        es_manual = payload.get("error_type") == "manual-report"
        tope = (
            self.settings.playtest_manual_reports_per_minute
            if es_manual
            else self.settings.playtest_incidents_per_minute
        )
        tipo_filter = (
            "json_extract(payload_json, '$.error_type')='manual-report'"
            if es_manual
            else "(json_extract(payload_json, '$.error_type') IS NULL"
            " OR json_extract(payload_json, '$.error_type')!='manual-report')"
        )
        recent = await self.db.fetchone(
            "SELECT COUNT(*) AS c FROM playtest_occurrences"
            " WHERE COALESCE(NULLIF(session_id,''), game_id, 'sin-sesion')=?"
            f" AND timestamp_utc > ? AND {tipo_filter}",
            (bucket, (datetime.now(UTC) - timedelta(minutes=1)).isoformat()),
        )
        if recent and recent["c"] >= tope:
            raise ValueError("incident rate limited")
        clean = redact(payload)
        fp = str(payload.get("fingerprint") or fingerprint_for(clean))
        now = utc_now()
        row = await self.db.fetchone("SELECT * FROM playtest_incidents WHERE fingerprint=?", (fp,))
        severity = str(payload.get("severity") or suggested_severity(clean)).upper()
        category = str(payload.get("category") or "other")[:80]
        title = str(payload.get("title") or payload.get("message") or category)[:140]
        player_id = payload.get("player_id")
        game_id = payload.get("game_id")
        build = str(payload.get("build_version") or self.settings.playtest_build or "unknown")[:120]
        if row is None:
            for _ in range(3):
                count = (await self.db.fetchone("SELECT COUNT(*) AS c FROM playtest_incidents"))["c"] + 1
                incident_id = str(uuid.uuid4())
                code = f"PLAY-{count:03d}"
                try:
                    await self.db.execute(
                        """
                        INSERT INTO playtest_incidents
                          (id, code, title, category, severity, status, fingerprint, frequency,
                           players_json, games_json, first_seen_at, last_seen_at, first_build, last_build, evidence_json, steps_json)
                        VALUES (?, ?, ?, ?, ?, 'new', ?, 0, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            incident_id, code, title, category, severity, fp,
                            json.dumps([player_id] if player_id else []),
                            json.dumps([game_id] if game_id else []),
                            now, now, build, build,
                            json.dumps({}), json.dumps(clean.get("action_trail") or []),
                        ),
                    )
                    break
                except sqlite3.IntegrityError:
                    row = await self.db.fetchone("SELECT * FROM playtest_incidents WHERE fingerprint=?", (fp,))
                    if row is not None:
                        break
            else:
                raise RuntimeError("could not create playtest incident")
        if row is not None:
            incident_id = row["id"]
            code = row["code"]
            players = set(json.loads(row["players_json"] or "[]"))
            games = set(json.loads(row["games_json"] or "[]"))
            if player_id:
                players.add(player_id)
            if game_id:
                games.add(game_id)
            await self.db.execute(
                """
                UPDATE playtest_incidents SET last_seen_at=?, last_build=?,
                  players_json=?, games_json=? WHERE id=?
                """,
                (now, build, json.dumps(sorted(players)), json.dumps(sorted(games)), incident_id),
            )
        occ_id = str(uuid.uuid4())
        await self.db.execute(
            """
            INSERT INTO playtest_occurrences
              (id, incident_id, session_id, game_id, player_id, player_alias, request_id, event_id,
               sequence_number, build_version, timestamp_utc, timestamp_local, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                occ_id, incident_id, payload.get("session_id"), game_id, player_id,
                str(payload.get("player_alias") or "")[:80], payload.get("request_id"), payload.get("event_id"),
                payload.get("sequence_number"), build, now, str(payload.get("timestamp_local") or "")[:80],
                json.dumps(clean, ensure_ascii=False),
            ),
        )
        await self.db.execute("UPDATE playtest_incidents SET frequency=frequency+1, last_seen_at=? WHERE id=?", (now, incident_id))
        return {"incident_id": code, "occurrence_id": occ_id, "fingerprint": fp}

    async def add_attachment(self, incident_code: str, occurrence_id: str | None, data_url: str) -> dict[str, Any]:
        row = await self.db.fetchone("SELECT * FROM playtest_incidents WHERE code=?", (incident_code,))
        if row is None:
            raise ValueError("incident not found")
        head, _, body = data_url.partition(",")
        mime = head.removeprefix("data:").split(";")[0]
        if mime not in {"image/png", "image/jpeg", "image/webp"}:
            raise ValueError("invalid mime")
        raw = base64.b64decode(body, validate=True)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError("attachment too large")
        ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}[mime]
        aid = str(uuid.uuid4())
        filename = aid + ext
        path = self.attach_dir / filename
        path.write_bytes(raw)
        await self.db.execute(
            "INSERT INTO playtest_attachments (id, incident_id, occurrence_id, filename, mime, size_bytes, path, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (aid, row["id"], occurrence_id, filename, mime, len(raw), str(path), utc_now()),
        )
        return {"attachment_id": aid}

    async def list_admin(self, filters: dict[str, str]) -> dict[str, Any]:
        where: list[str] = []
        params: list[Any] = []
        for field in ("severity", "category", "status"):
            if filters.get(field):
                where.append(f"{field}=?")
                params.append(filters[field])
        if filters.get("build"):
            where.append("(first_build=? OR last_build=?)")
            params.extend([filters["build"], filters["build"]])
        sql = "SELECT * FROM playtest_incidents"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY CASE severity WHEN 'BLOCKER' THEN 1 WHEN 'CRITICAL' THEN 2 WHEN 'MAJOR' THEN 3 ELSE 4 END, last_seen_at DESC"
        incidents = [dict(r) for r in await self.db.fetchall(sql, tuple(params))]
        sessions = await self.db.fetchone("SELECT COUNT(*) AS c FROM playtest_sessions")
        games = await self.db.fetchone("SELECT COUNT(DISTINCT game_id) AS c FROM playtest_sessions WHERE game_id IS NOT NULL")
        for inc in incidents:
            inc["players"] = json.loads(inc.pop("players_json") or "[]")
            inc["games"] = json.loads(inc.pop("games_json") or "[]")
            inc["evidence"] = json.loads(inc.pop("evidence_json") or "{}")
            inc["steps"] = json.loads(inc.pop("steps_json") or "[]")
        return {"status": self.status(), "sessions": sessions["c"], "games": games["c"], "incidents": incidents}

    async def incident_detail(self, code: str) -> dict[str, Any]:
        inc = await self.db.fetchone("SELECT * FROM playtest_incidents WHERE code=?", (code,))
        if inc is None:
            raise ValueError("not found")
        occ = [dict(r) for r in await self.db.fetchall(
            "SELECT * FROM playtest_occurrences WHERE incident_id=? ORDER BY timestamp_utc DESC LIMIT 100", (inc["id"],)
        )]
        trail = []
        if occ:
            sid = occ[0].get("session_id")
            trail = [dict(r) for r in await self.db.fetchall(
                "SELECT * FROM playtest_action_trail WHERE session_id=? ORDER BY timestamp_utc DESC LIMIT 50", (sid,)
            )]
        attachments = [dict(r) for r in await self.db.fetchall("SELECT id, filename, mime, size_bytes, created_at FROM playtest_attachments WHERE incident_id=?", (inc["id"],))]
        return {"incident": dict(inc), "occurrences": occ, "trail": trail, "attachments": attachments}

    async def triage(self, code: str, status: str | None, severity: str | None, note: str | None) -> dict[str, Any]:
        row = await self.db.fetchone("SELECT * FROM playtest_incidents WHERE code=?", (code,))
        if row is None:
            raise ValueError("not found")
        new_status = status or row["status"]
        new_sev = (severity or row["severity"]).upper()
        await self.db.execute(
            "UPDATE playtest_incidents SET status=?, severity=? WHERE code=?",
            (new_status, new_sev, code),
        )
        await self.db.execute(
            "INSERT INTO playtest_status_changes (id, incident_id, status_from, status_to, severity_from, severity_to, note, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), row["id"], row["status"], new_status, row["severity"], new_sev, (note or "")[:1000], utc_now()),
        )
        return {"ok": True}

    async def export(self, root: str | None = None) -> dict[str, Any]:
        root = root or self.settings.playtest_export_dir
        out = Path(root)
        out.mkdir(parents=True, exist_ok=True)
        data = await self.list_admin({})
        incidents = data["incidents"]
        (out / "incidents.json").write_text(json.dumps(incidents, ensure_ascii=False, indent=2), encoding="utf-8")
        with (out / "incidents.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["code", "title", "severity", "status", "category", "frequency", "first_seen_at", "last_seen_at", "first_build", "last_build"])
            writer.writeheader()
            for inc in incidents:
                writer.writerow({k: inc.get(k, "") for k in writer.fieldnames})
        lines = ["# Playtest Backlog", "", f"Generado: {utc_now()}", ""]
        for sev in ("BLOCKER", "CRITICAL", "MAJOR", "MINOR"):
            group = [i for i in incidents if i["severity"] == sev]
            if not group:
                continue
            lines += [f"## {sev}", ""]
            for inc in group:
                lines += [
                    f"### {inc['code']} - {inc['title']}",
                    f"- Severidad: {inc['severity']}",
                    f"- Estado: {inc['status']}",
                    f"- Frecuencia: {inc['frequency']}",
                    f"- Jugadores afectados: {', '.join(inc['players']) or '-'}",
                    f"- Partidas afectadas: {', '.join(inc['games']) or '-'}",
                    f"- Primera aparición: {inc['first_seen_at']}",
                    f"- Última aparición: {inc['last_seen_at']}",
                    f"- Descripción: {inc['title']}",
                    f"- Pasos reconstruidos: revisar ocurrencias y action trail del panel.",
                    f"- Evidencia: adjuntos/ocurrencias en panel admin.",
                    f"- Workaround: {inc.get('workaround') or '-'}",
                    "- Criterio de aceptación sugerido: reproducir el flujo sin que reaparezca este fingerprint.",
                    "",
                ]
        (out / "backlog.md").write_text("\\n".join(lines), encoding="utf-8")
        summary = [
            "# Playtest Session Summary",
            "",
            f"Generado: {utc_now()}",
            f"Modo activo: {data['status']['active']}",
            f"Build: {data['status']['build']}",
            f"Sesiones: {data['sessions']}",
            f"Partidas: {data['games']}",
            f"Incidentes: {len(incidents)}",
            "",
        ]
        (out / "session-summary.md").write_text("\\n".join(summary), encoding="utf-8")
        return {"ok": True, "files": [str(out / n) for n in ("backlog.md", "session-summary.md", "incidents.json", "incidents.csv")]}

    async def purge_old(self, days: int | None = None, delete_attachments: bool = False, keep_confirmed: bool = True) -> dict[str, Any]:
        cutoff = (datetime.now(UTC) - timedelta(days=days or self.settings.playtest_retention_days)).isoformat()
        old = await self.db.fetchall("SELECT id, status FROM playtest_incidents WHERE last_seen_at < ?", (cutoff,))
        deleted = 0
        for row in old:
            if keep_confirmed and row["status"] in {"confirmed", "investigating", "retest"}:
                continue
            if delete_attachments:
                for att in await self.db.fetchall("SELECT path FROM playtest_attachments WHERE incident_id=?", (row["id"],)):
                    try:
                        Path(att["path"]).unlink(missing_ok=True)
                    except Exception:
                        pass
            for table in ("playtest_attachments", "playtest_occurrences", "playtest_status_changes"):
                await self.db.execute(f"DELETE FROM {table} WHERE incident_id=?", (row["id"],))
            await self.db.execute("DELETE FROM playtest_incidents WHERE id=?", (row["id"],))
            deleted += 1
        return {"ok": True, "deleted": deleted}
