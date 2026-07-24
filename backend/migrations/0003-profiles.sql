-- Perfiles persistentes del grupo: identidad entre partidas, sin contraseña.
CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY,
    nickname TEXT NOT NULL,
    color TEXT,
    avatar_asset_id TEXT,
    -- link personal permanente: solo el hash SHA-256 del token
    token_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

ALTER TABLE players ADD COLUMN profile_id TEXT REFERENCES profiles(id);
CREATE INDEX IF NOT EXISTS idx_players_profile ON players(profile_id);
