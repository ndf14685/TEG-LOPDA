-- Snapshot del estado del motor al inicio de cada turno (base del replay).
CREATE TABLE IF NOT EXISTS turn_snapshots (
    game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    state_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (game_id, turn_number)
);
