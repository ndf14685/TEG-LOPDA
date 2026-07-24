"""Perfiles persistentes: CRUD admin, link personal e invitación por perfil."""

from conftest import ADMIN


def test_profile_lifecycle_and_invite(client):
    # crear perfil
    resp = client.post("/api/admin/profiles", json={"nickname": "Daro", "color": "red"}, headers=ADMIN)
    assert resp.status_code == 200, resp.text
    created = resp.json()
    token = created["token"]
    pid = created["profile"]["id"]
    assert created["profile_url"].endswith(token)

    # listar
    resp = client.get("/api/admin/profiles", headers=ADMIN)
    assert any(p["id"] == pid for p in resp.json()["profiles"])

    # link personal resuelve sin auth
    resp = client.get(f"/api/profile/{token}")
    assert resp.status_code == 200
    assert resp.json()["profile"]["nickname"] == "Daro"
    assert client.get("/api/profile/token-falso").status_code == 404

    # regenerar invalida el anterior
    resp = client.post(f"/api/admin/profiles/{pid}/regenerate-token", headers=ADMIN)
    new_token = resp.json()["token"]
    assert client.get(f"/api/profile/{token}").status_code == 404
    assert client.get(f"/api/profile/{new_token}").status_code == 200

    # invitar por perfil: hereda apodo y color, y queda vinculado
    game = client.post("/api/admin/games", json={"name": "con-perfiles"}, headers=ADMIN).json()["game"]
    resp = client.post(
        f"/api/admin/games/{game['id']}/players",
        json={"profile_id": pid},
        headers=ADMIN,
    )
    assert resp.status_code == 200, resp.text
    player = resp.json()["player"]
    assert player["nickname"] == "Daro"
    assert player["color"] == "red"
    assert player["profile_id"] == pid


def test_invite_without_profile_still_works(client):
    game = client.post("/api/admin/games", json={"name": "sin-perfiles"}, headers=ADMIN).json()["game"]
    resp = client.post(
        f"/api/admin/games/{game['id']}/players",
        json={"nickname": "Suelto"},
        headers=ADMIN,
    )
    assert resp.status_code == 200
    assert resp.json()["player"]["profile_id"] is None
