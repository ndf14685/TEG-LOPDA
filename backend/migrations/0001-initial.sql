-- Esquema inicial TEG LOPDA.

CREATE TABLE IF NOT EXISTS games (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'lobby',
    config_json TEXT NOT NULL DEFAULT '{}',
    state_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS players (
    id TEXT PRIMARY KEY,
    game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    nickname TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'player',
    color TEXT,
    avatar_asset_id TEXT,
    -- solo se guarda el hash SHA-256 del token; el token en claro se muestra
    -- una única vez al admin al crearlo o regenerarlo
    token_hash TEXT,
    token_revoked INTEGER NOT NULL DEFAULT 0,
    nickname_editable INTEGER NOT NULL DEFAULT 1,
    is_ready INTEGER NOT NULL DEFAULT 0,
    eliminated INTEGER NOT NULL DEFAULT 0,
    joined_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_players_game ON players(game_id);
CREATE INDEX IF NOT EXISTS idx_players_token ON players(game_id, token_hash);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    actor_id TEXT,
    target_id TEXT,
    visibility TEXT NOT NULL DEFAULT 'public',
    schema_version TEXT NOT NULL DEFAULT '1.0.0',
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (game_id, sequence_number)
);

CREATE INDEX IF NOT EXISTS idx_events_game_seq ON events(game_id, sequence_number);

-- Audios personalizados: solo asset IDs lógicos, nunca rutas físicas.
CREATE TABLE IF NOT EXISTS taunt_assets (
    id TEXT PRIMARY KEY,
    game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    owner_player_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    target_player_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (game_id, owner_player_id, target_player_id, event_type)
);
