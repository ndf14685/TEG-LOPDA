"""Audios personalizados por perfil: subida, límites, servido y disparo."""

from conftest import ADMIN


def _profile(client, nickname):
    r = client.post("/api/admin/profiles", json={"nickname": nickname}, headers=ADMIN)
    return r.json()


def test_upload_list_serve_delete(client):
    daro = _profile(client, "Daro")
    lord = _profile(client, "Lord")
    body = b"\x1aE\xdf\xa3" + b"x" * 100  # bytes cualesquiera, el server no decodifica

    r = client.post(
        f"/api/profile/{daro['token']}/taunts",
        params={"target_profile_id": lord["profile"]["id"],
                "event_type": "territory.conquered", "ext": "webm"},
        content=body,
    )
    assert r.status_code == 200, r.text
    taunt = r.json()["taunt"]
    assert taunt["audio_url"].startswith("/api/media/taunts/")

    # listar
    r = client.get(f"/api/profile/{daro['token']}/taunts")
    assert len(r.json()["taunts"]) == 1

    # servir
    r = client.get(taunt["audio_url"])
    assert r.status_code == 200 and r.content == body

    # reemplazo: mismo par+evento pisa el anterior
    r2 = client.post(
        f"/api/profile/{daro['token']}/taunts",
        params={"target_profile_id": lord["profile"]["id"],
                "event_type": "territory.conquered", "ext": "mp3"},
        content=b"nuevo-audio",
    )
    assert r2.status_code == 200
    r = client.get(f"/api/profile/{daro['token']}/taunts")
    assert len(r.json()["taunts"]) == 1

    # borrar
    tid = r.json()["taunts"][0]["id"]
    assert client.delete(f"/api/profile/{daro['token']}/taunts/{tid}").status_code == 200
    assert client.get(f"/api/profile/{daro['token']}/taunts").json()["taunts"] == []


def test_upload_limits_and_validation(client):
    daro = _profile(client, "Daro")
    lord = _profile(client, "Lord")
    params = {"target_profile_id": lord["profile"]["id"], "event_type": "player.eliminated"}

    big = b"x" * (600 * 1024)
    assert client.post(f"/api/profile/{daro['token']}/taunts", params=params, content=big).status_code == 413
    assert client.post(
        f"/api/profile/{daro['token']}/taunts",
        params={**params, "event_type": "hack.evento"}, content=b"x",
    ).status_code == 422
    assert client.post(
        f"/api/profile/{daro['token']}/taunts",
        params={"target_profile_id": daro["profile"]["id"], "event_type": "player.eliminated"},
        content=b"x",
    ).status_code == 422
    assert client.get("/api/media/taunts/../../../etc/passwd").status_code in (404, 422)
