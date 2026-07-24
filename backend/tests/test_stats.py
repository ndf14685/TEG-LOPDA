"""Estadísticas reales calculadas del event log."""

from teg_backend.application.stats import assign_trophies, compute_stats

PLAYERS = [
    {"id": "a", "nickname": "Daro", "role": "player"},
    {"id": "b", "nickname": "Lord", "role": "player"},
]


def _ev(etype, actor=None, target=None, payload=None, ts="2026-07-24T00:00:00+00:00"):
    return {"event_type": etype, "actor_id": actor, "target_id": target,
            "payload": payload or {}, "timestamp": ts}


def test_dice_and_combat_counters():
    events = [
        _ev("dice.rolled", "a", payload={"dice": [6, 6, 1]}),
        _ev("attack.resolved", "a", "b",
            payload={"attacker_dice": [6, 3], "defender_dice": [1],
                     "attacker_losses": 0, "defender_losses": 1}),
        _ev("attack.resolved", "a", "b",
            payload={"attacker_dice": [1], "defender_dice": [6],
                     "attacker_losses": 1, "defender_losses": 0}),
        _ev("territory.conquered", "a", "b"),
        _ev("player.eliminated", "a", "b"),
    ]
    stats = compute_stats(events, PLAYERS)
    assert stats["a"]["dice_six"] == 3 and stats["a"]["dice_one"] == 2
    assert stats["a"]["attacks_launched"] == 2
    assert stats["a"]["attacks_won"] == 1 and stats["a"]["attacks_lost"] == 1
    assert stats["b"]["defenses_perfect"] == 1
    assert stats["a"]["conquests"] == 1 and stats["b"]["territories_lost"] == 1
    assert stats["a"]["eliminations"] == 1 and stats["b"]["was_eliminated"] is True


def test_whiner_and_pacts_and_trophies():
    events = [
        _ev("pact.proposed", "a", "b"),
        _ev("pact.broken", "a", "b", payload={"betrayal": True}),
        _ev("attack.resolved", "b", "a",
            payload={"attacker_dice": [2], "defender_dice": [5],
                     "attacker_losses": 1, "defender_losses": 0},
            ts="2026-07-24T00:00:00+00:00"),
        _ev("chat.message", "b", ts="2026-07-24T00:00:10+00:00"),  # lloró a los 10s
        _ev("chat.message", "b", ts="2026-07-24T00:10:00+00:00"),  # tarde: no cuenta
    ]
    stats = compute_stats(events, PLAYERS)
    assert stats["a"]["pacts_proposed"] == 1
    assert stats["a"]["betrayals"] == 1
    assert stats["b"]["whines"] == 1 and stats["b"]["chat_messages"] == 2

    trophies = assign_trophies(stats)
    titles_a = {t["title"] for t in trophies["a"]}
    titles_b = {t["title"] for t in trophies["b"]}
    assert "Más Traidor" in titles_a and "Vendehumo" in titles_a
    assert "Más Llorón" in titles_b
    # nadie sacó un 6: el trofeo no se inventa
    assert "Rey del Seis" not in titles_a | titles_b
