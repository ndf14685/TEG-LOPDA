"""Cotas del lado servidor para incidentes de playtest.

El instrumento genero payloads de hasta 882 KB y 41 ocurrencias en una sola
partida. Aunque el cliente ya no se desboque, el servidor no debe aceptarlo.
"""


def test_rechaza_trail_desmedido(client):
    """action_trail y recent_errors eran list[dict] sin cota."""
    resp = client.post("/api/playtest/incidents", json={
        "category": "other", "title": "x", "error_type": "test",
        "action_trail": [{"a": "b"}] * 500,
    })
    assert resp.status_code == 422


def test_throttle_alcanza_a_los_incidentes_automaticos(client):
    """Antes el rate limit solo miraba manual-report; los automaticos
    (pending-action-timeout, sequence-gap) entraban sin freno.

    `active` es una property de solo lectura derivada de `settings.playtest_mode`
    / `settings.playtest_until`; se activa el modo playtest seteando el
    atributo del que deriva, sin agregarle un setter a PlaytestService solo
    para el test.
    """
    client.app.state.playtest.settings.playtest_mode = True
    tope = client.app.state.playtest.settings.playtest_incidents_per_minute
    aceptados = 0
    for _ in range(40):
        resp = client.post("/api/playtest/incidents", json={
            "category": "other", "title": "spam",
            "error_type": "pending-action-timeout", "session_id": "s1",
        })
        if resp.status_code == 200:
            aceptados += 1
    assert aceptados <= tope, "el throttle no freno los incidentes automaticos al tope configurado"


def test_agotar_cupo_automatico_no_bloquea_manual_report(client):
    """Los contadores son independientes: gastar la cuota de incidentes
    automaticos no debe consumir la cuota de manual-report, que es la que
    protege el reporte valioso del jugador.
    """
    client.app.state.playtest.settings.playtest_mode = True
    tope_auto = client.app.state.playtest.settings.playtest_incidents_per_minute
    for _ in range(tope_auto + 5):
        client.post("/api/playtest/incidents", json={
            "category": "other", "title": "spam",
            "error_type": "pending-action-timeout", "session_id": "s2",
        })
    resp = client.post("/api/playtest/incidents", json={
        "category": "other", "title": "reporte real",
        "error_type": "manual-report", "session_id": "s2",
    })
    assert resp.status_code == 200, "un manual-report no deberia perder su cupo por incidentes automaticos"
