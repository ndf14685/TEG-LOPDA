/** Reacciones rápidas del tablero. Compartidas: viajan por el broadcast de
 * chat y flotan en la pantalla de todos (incluidos los que esperan turno). */
export const REACTION_EMOJIS = ['🍿', '💀', '🤡', '🔥', '💩', '💸'] as const;

export const REACTION_SET: ReadonlySet<string> = new Set(REACTION_EMOJIS);
