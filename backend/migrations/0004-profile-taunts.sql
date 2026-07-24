-- Audios personalizados por perfil: owner graba contra target por tipo de evento.
CREATE TABLE IF NOT EXISTS profile_taunts (
    id TEXT PRIMARY KEY,
    owner_profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    target_profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    filename TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (owner_profile_id, target_profile_id, event_type)
);
