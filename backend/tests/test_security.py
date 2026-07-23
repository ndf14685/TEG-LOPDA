from teg_backend.security.sanitize import is_valid_asset_id, sanitize_nickname, sanitize_text
from teg_backend.security.tokens import hash_token, new_game_code, new_player_token, verify_token


def test_tokens_random_and_verifiable():
    t1, t2 = new_player_token(), new_player_token()
    assert t1 != t2
    assert len(t1) >= 30
    assert verify_token(t1, hash_token(t1))
    assert not verify_token(t2, hash_token(t1))


def test_game_code_charset():
    code = new_game_code()
    assert len(code) == 8
    assert all(c in "abcdefghjkmnpqrstuvwxyz23456789" for c in code)


def test_sanitize_text_strips_control_chars():
    assert sanitize_text("hola\x00\x1bmundo") == "holamundo"
    assert sanitize_text("  espacios   raros  ") == "espacios raros"
    assert len(sanitize_text("x" * 1000)) == 500


def test_sanitize_nickname():
    assert sanitize_nickname("Daro\n el capo") == "Daro el capo"
    assert len(sanitize_nickname("a" * 100)) <= 24


def test_asset_id_validation():
    assert is_valid_asset_id("audio/taunts/player-nessi/to-player-daro/territory-conquered-001.ogg")
    assert not is_valid_asset_id("../../etc/passwd")
    assert not is_valid_asset_id("/audio/x.ogg")
    assert not is_valid_asset_id("audio/../secret.ogg")
    assert not is_valid_asset_id("video/x.mp4")


def test_join_with_bad_token_is_generic_404(client):
    resp = client.get("/api/join/nocode/notoken")
    assert resp.status_code == 404
