from conftest import ADMIN


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert set(body) == {"status", "version"}  # sin info sensible


def test_metrics_local(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "active_connections" in resp.json()


def test_admin_requires_token(client):
    assert client.post("/api/admin/games", json={"name": "x"}).status_code == 401
    assert client.get("/api/admin/games", headers={"X-Admin-Token": "malo"}).status_code == 401
    assert client.get("/api/admin/games", headers=ADMIN).status_code == 200
