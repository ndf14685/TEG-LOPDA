"""Estadísticas de partida: se calculan del event log al terminar.

Funciones puras: eventos + jugadores entran, contadores y trofeos salen.
Los trofeos absurdos son parte del juego, no decoración: cada uno se asigna
solo si el dato real lo respalda.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _empty() -> dict[str, Any]:
    return {
        "dice_six": 0, "dice_one": 0, "dice_total": 0,
        "attacks_launched": 0, "attacks_won": 0, "attacks_lost": 0,
        "defenses_perfect": 0,
        "conquests": 0, "territories_lost": 0,
        "eliminations": 0, "was_eliminated": False,
        "pacts_proposed": 0, "pacts_broken": 0, "betrayals": 0,
        "cards_traded": 0, "chat_messages": 0, "whines": 0,
    }


def _ts(event: dict) -> float:
    try:
        return datetime.fromisoformat(event["timestamp"]).timestamp()
    except Exception:
        return 0.0


def compute_stats(events: list[dict], players: list[dict]) -> dict[str, dict[str, Any]]:
    """Contadores por jugador a partir del historial persistido."""
    stats: dict[str, dict[str, Any]] = {
        p["id"]: _empty() for p in players if p["role"] in ("player", "ai_player")
    }
    last_combat_loss_at: dict[str, float] = {}

    def bump(pid: str | None, key: str, n: int = 1) -> None:
        if pid in stats:
            stats[pid][key] += n

    for ev in events:
        etype = ev.get("event_type")
        actor = ev.get("actor_id")
        target = ev.get("target_id")
        payload = ev.get("payload") or {}

        if etype == "dice.rolled":
            for d in payload.get("dice", []):
                bump(actor, "dice_total")
                if d == 6:
                    bump(actor, "dice_six")
                elif d == 1:
                    bump(actor, "dice_one")
        elif etype == "attack.resolved":
            for d in payload.get("attacker_dice", []):
                bump(actor, "dice_total")
                if d == 6:
                    bump(actor, "dice_six")
                elif d == 1:
                    bump(actor, "dice_one")
            for d in payload.get("defender_dice", []):
                bump(target, "dice_total")
                if d == 6:
                    bump(target, "dice_six")
                elif d == 1:
                    bump(target, "dice_one")
            bump(actor, "attacks_launched")
            al = int(payload.get("attacker_losses", 0))
            dl = int(payload.get("defender_losses", 0))
            if al > dl:
                bump(actor, "attacks_lost")
                last_combat_loss_at[actor or ""] = _ts(ev)
            elif dl > al:
                bump(actor, "attacks_won")
                last_combat_loss_at[target or ""] = _ts(ev)
            if al > 0 and dl == 0:
                bump(target, "defenses_perfect")
        elif etype == "territory.conquered":
            bump(actor, "conquests")
            bump(target, "territories_lost")
        elif etype == "player.eliminated":
            bump(actor, "eliminations")
            if target in stats:
                stats[target]["was_eliminated"] = True
        elif etype == "pact.proposed":
            bump(actor, "pacts_proposed")
        elif etype == "pact.broken":
            bump(actor, "pacts_broken")
            if payload.get("betrayal"):
                bump(actor, "betrayals")
        elif etype == "cards.traded":
            bump(actor, "cards_traded")
        elif etype == "chat.message":
            bump(actor, "chat_messages")
            # llorón: chatear a los 30 segundos de perder un combate
            lost_at = last_combat_loss_at.get(actor or "")
            if lost_at and 0 <= _ts(ev) - lost_at <= 30:
                bump(actor, "whines")

    return stats


TROPHY_DEFS: list[dict[str, str]] = [
    {"id": "rey_del_seis", "metric": "dice_six", "title": "Rey del Seis",
     "icon": "🎲", "blurb": "Sacó más seises que nadie. Cómprenle un lotería."},
    {"id": "rey_del_uno", "metric": "dice_one", "title": "Rey del Uno",
     "icon": "🥴", "blurb": "Los dados lo odian con evidencia estadística."},
    {"id": "kamikaze", "metric": "attacks_lost", "title": "Kamikaze",
     "icon": "💥", "blurb": "Más ataques perdidos siendo atacante. Valor sin cálculo."},
    {"id": "mas_traidor", "metric": "betrayals", "title": "Más Traidor",
     "icon": "🗡️", "blurb": "Apuñaló aliados con la sonrisa puesta."},
    {"id": "vendehumo", "metric": "pacts_proposed", "title": "Vendehumo",
     "icon": "🚬", "blurb": "El que más pactos propuso. Diplomacia o verso."},
    {"id": "mas_agresivo", "metric": "attacks_launched", "title": "Más Agresivo",
     "icon": "😤", "blurb": "Atacó todo lo que se movía."},
    {"id": "la_muralla", "metric": "defenses_perfect", "title": "La Muralla",
     "icon": "🧱", "blurb": "Defensas perfectas: ni una baja propia."},
    {"id": "mas_paises_perdidos", "metric": "territories_lost", "title": "Más Países Perdidos",
     "icon": "🏳️", "blurb": "Su imperio fue un préstamo a corto plazo."},
    {"id": "mas_lloron", "metric": "whines", "title": "Más Llorón",
     "icon": "😭", "blurb": "Perdía un combate y corría al chat a quejarse."},
]


def assign_trophies(stats: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    """Cada trofeo va al máximo real (>0). Retorna player_id → trofeos."""
    trophies: dict[str, list[dict[str, str]]] = {pid: [] for pid in stats}
    for t in TROPHY_DEFS:
        best_pid, best_val = None, 0
        for pid, s in stats.items():
            val = int(s.get(t["metric"], 0))
            if val > best_val:
                best_pid, best_val = pid, val
        if best_pid is not None:
            trophies[best_pid].append(
                {"id": t["id"], "title": t["title"], "icon": t["icon"],
                 "blurb": t["blurb"], "value": str(best_val)}
            )
    return trophies
