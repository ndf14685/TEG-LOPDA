import pytest

from teg_backend.domain.engine import (
    EngineError, GameEngine, resolve_combat, roll_dice,
)


def test_roll_dice_bounds():
    for count in (1, 2, 3):
        dice = roll_dice(count)
        assert len(dice) == count
        assert all(1 <= d <= 6 for d in dice)
        assert dice == sorted(dice, reverse=True)
    for bad in (0, 4, -1):
        with pytest.raises(EngineError):
            roll_dice(bad)


def test_combat_defender_wins_ties():
    result = resolve_combat([6, 4, 3], [6, 4, 1])
    # 6vs6 y 4vs4 los gana el defensor; 3vs1 el atacante
    assert result.attacker_losses == 2
    assert result.defender_losses == 1


def test_combat_uneven_dice():
    result = resolve_combat([5], [6, 6, 6])
    assert result.attacker_losses == 1
    assert result.defender_losses == 0
    assert len(result.comparisons) == 1


def test_turn_rotation_and_removal():
    engine = GameEngine()
    with pytest.raises(EngineError):
        engine.start(["solo"])
    turn = engine.start(["a", "b", "c"])
    first = turn.current_player_id
    engine.advance_turn()
    assert engine.turn.current_player_id != first
    # sacar al jugador actual mantiene el orden coherente
    current = engine.turn.current_player_id
    engine.remove_player(current)
    assert current not in engine.turn.order
    assert engine.turn.current_player_id in engine.turn.order


def test_engine_serialization_roundtrip():
    engine = GameEngine()
    engine.start(["a", "b"])
    engine.advance_turn()
    restored = GameEngine.from_dict(engine.to_dict())
    assert restored.turn.to_dict() == engine.turn.to_dict()


def test_wager_win_pays_double_next_turn():
    engine = GameEngine()
    engine.start(["a", "b"])
    engine.stage = "turns"
    cur = engine.turn.current_player_id
    engine.turn.phase = "reinforcement"
    engine.turn.reinforcements_available = 5
    engine.set_wager(cur, 2)
    assert engine.turn.reinforcements_available == 3
    assert engine.turn.wager == 2
    engine.register_conquest(cur)
    base = engine.calculate_reinforcements(cur)  # base sin bono (aún no resuelto)
    res = engine.resolve_wager(cur)
    assert res == {"player_id": cur, "won": True, "wagered": 2, "payout": 4}
    assert engine.turn.wager == 0
    # el bono (4) se cobra una sola vez en el próximo cálculo de refuerzos
    assert engine.calculate_reinforcements(cur) == base + 4
    assert engine.calculate_reinforcements(cur) == base


def test_wager_loss_forfeits_no_bonus():
    engine = GameEngine()
    engine.start(["a", "b"])
    engine.stage = "turns"
    cur = engine.turn.current_player_id
    engine.turn.phase = "reinforcement"
    engine.turn.reinforcements_available = 4
    engine.set_wager(cur, 3)
    assert engine.turn.reinforcements_available == 1
    base = engine.calculate_reinforcements(cur)
    res = engine.resolve_wager(cur)  # sin conquista
    assert res == {"player_id": cur, "won": False, "wagered": 3, "payout": 0}
    assert engine.calculate_reinforcements(cur) == base  # sin bono


def test_wager_validation():
    engine = GameEngine()
    engine.start(["a", "b"])
    engine.stage = "turns"
    cur = engine.turn.current_player_id
    engine.turn.phase = "reinforcement"
    engine.turn.reinforcements_available = 2
    with pytest.raises(EngineError):
        engine.set_wager(cur, 0)
    with pytest.raises(EngineError):
        engine.set_wager(cur, 5)
    engine.turn.phase = "attack"
    with pytest.raises(EngineError):
        engine.set_wager(cur, 1)
    assert engine.resolve_wager(cur) is None
