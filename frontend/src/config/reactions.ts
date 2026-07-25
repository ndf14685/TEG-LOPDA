/** Reacciones rápidas del tablero. Compartidas: viajan por el broadcast de
 * chat y flotan en la pantalla de todos (incluidos los que esperan turno). */
export const REACTION_EMOJIS = ['🍿', '💀', '🤡', '🔥', '💩', '💸'] as const;

export const REACTION_SET: ReadonlySet<string> = new Set(REACTION_EMOJIS);

/** Etiquetas de respaldo cuando el navegador no renderiza emoji a color. */
export const REACTION_LABELS: Record<string, string> = {
  '🍿': 'pochoclos',
  '💀': 'muerto',
  '🤡': 'payaso',
  '🔥': 'fuego',
  '💩': 'desastre',
  '💸': 'fichas',
};
