-- Secuencia densa sobre eventos publicos unicamente.
-- sequence_number sigue siendo el orden de almacenamiento (denso sobre TODO).
-- public_sequence es lo que viaja al cliente: sin huecos para quien solo ve publicos.
-- NULL para privados y de admin.
ALTER TABLE events ADD COLUMN public_sequence INTEGER;

CREATE INDEX IF NOT EXISTS idx_events_game_public_seq
    ON events(game_id, public_sequence);

-- Backfill de partidas ya jugadas: numera los publicos por orden de almacenamiento.
UPDATE events
   SET public_sequence = (
        SELECT COUNT(*)
          FROM events AS previos
         WHERE previos.game_id = events.game_id
           AND previos.visibility = 'public'
           AND previos.sequence_number <= events.sequence_number
   )
 WHERE visibility = 'public';
