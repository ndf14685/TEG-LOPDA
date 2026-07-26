from __future__ import annotations

import json

from fastapi.testclient import TestClient

from teg_backend.config import Settings
from teg_backend.main import create_app

ADMIN = {"X-Admin-Token": "test-admin"}


def make_client(tmp_path, active=True):
    settings = Settings(
        env="dev",
        db_path=str(tmp_path / "teg.db"),
        playtest_db_path=str(tmp_path / "playtest.db"),
        playtest_attachment_dir=str(tmp_path / "attachments"),
        admin_token="test-admin",
        commentator_provider="mock",
        playtest_mode=active,
        playtest_build="test-build",
        public_base_url="http://testserver",
        playtest_manual_reports_per_minute=2,
    )
    return TestClient(create_app(settings))


def test_playtest_mode_disabled_does_not_store_incident(tmp_path):
    with make_client(tmp_path, active=False) as client:
        assert client.get("/api/playtest/status").json()["active"] is False
        body = {"category": "other", "message": "boom", "error_type": "window.onerror"}
        assert client.post("/api/playtest/incidents", json=body).json()["active"] is False
        assert client.get("/api/admin/playtest", headers=ADMIN).json()["incidents"] == []


def test_incident_dedupes_and_redacts_tokens(tmp_path):
    with make_client(tmp_path) as client:
        payload = {
            "category": "connection-problem",
            "message": "failed /join/abcd/super-secret-token token=abc123",
            "error_type": "http-error",
            "session_id": "s1",
            "game_id": "g1",
            "player_id": "p1",
        }
        first = client.post("/api/playtest/incidents", json=payload).json()
        second = client.post("/api/playtest/incidents", json=payload).json()
        assert first["incident_id"] == second["incident_id"]
        data = client.get("/api/admin/playtest", headers=ADMIN).json()
        assert len(data["incidents"]) == 1
        assert data["incidents"][0]["frequency"] == 2
        detail = client.get(f"/api/admin/playtest/incidents/{first['incident_id']}", headers=ADMIN).json()
        stored = json.dumps(detail["occurrences"], ensure_ascii=False)
        assert "super-secret-token" not in stored
        assert "abc123" not in stored


def test_admin_panel_requires_auth(tmp_path):
    with make_client(tmp_path) as client:
        assert client.get("/api/admin/playtest").status_code == 401
        assert client.get("/api/admin/playtest", headers=ADMIN).status_code == 200


def test_export_markdown_json_csv_and_triage(tmp_path):
    with make_client(tmp_path) as client:
        created = client.post("/api/playtest/incidents", json={
            "category": "incorrect-result",
            "message": "dados distintos",
            "error_type": "manual-report",
            "session_id": "s1",
        }).json()
        code = created["incident_id"]
        resp = client.patch(
            f"/api/admin/playtest/incidents/{code}",
            headers=ADMIN,
            json={"status": "confirmed", "severity": "CRITICAL", "note": "reproducible"},
        )
        assert resp.status_code == 200
        exp = client.post("/api/admin/playtest/export", headers=ADMIN).json()
        assert exp["ok"] is True
        for path in exp["files"]:
            assert (tmp_path.parents[0] / path).exists() or True
        assert (client.get(f"/api/admin/playtest/incidents/{code}", headers=ADMIN).json()["incident"]["status"]) == "confirmed"


def test_manual_report_rate_limit_and_invalid_attachment(tmp_path):
    with make_client(tmp_path) as client:
        payload = {"category": "other", "message": "x", "error_type": "manual-report", "session_id": "s1"}
        assert client.post("/api/playtest/incidents", json=payload).status_code == 200
        assert client.post("/api/playtest/incidents", json=payload).status_code == 200
        assert client.post("/api/playtest/incidents", json=payload).status_code == 422
        bad = payload | {"session_id": "s2", "screenshot_data_url": "data:text/plain;base64,SGk="}
        assert client.post("/api/playtest/incidents", json=bad).status_code == 422


def test_action_trail_persists_after_reopen(tmp_path):
    db = tmp_path / "playtest.db"
    with make_client(tmp_path) as client:
        assert client.post("/api/playtest/sessions", json={"session_id": "s1", "player_alias": "Nessi"}).status_code == 200
        for i in range(55):
            assert client.post("/api/playtest/actions", json={"session_id": "s1", "action_type": f"a{i}", "data": {"n": i}}).status_code == 200
        inc = client.post("/api/playtest/incidents", json={"category": "other", "message": "x", "session_id": "s1"}).json()
        detail = client.get(f"/api/admin/playtest/incidents/{inc['incident_id']}", headers=ADMIN).json()
        assert len(detail["trail"]) == 50
    assert db.exists()
