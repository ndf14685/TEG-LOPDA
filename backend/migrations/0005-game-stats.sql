-- Estadísticas por partida y jugador, calculadas del event log al terminar.
CREATE TABLE IF NOT EXISTS game_stats (
    game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    player_id TEXT NOT NULL,
    profile_id TEXT,
    stats_json TEXT NOT NULL,
    trophies_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (game_id, player_id)
);
CREATE INDEX IF NOT EXISTS idx_game_stats_profile ON game_stats(profile_id);
