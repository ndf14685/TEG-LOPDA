import type { BrandPalette } from '@teg/contracts';

/**
 * El backend guarda color como string libre (≤16). La paleta canónica la
 * define Dirección de Arte (assets/brand/palette/palette.json): al cargar,
 * applyPalette() pisa las CSS variables con sus valores WCAG AA.
 */
const COLOR_VALUES: Record<string, string> = {
  red: 'var(--player-red)',
  blue: 'var(--player-blue)',
  green: 'var(--player-green)',
  yellow: 'var(--player-yellow)',
  purple: 'var(--player-purple)',
  orange: 'var(--player-orange)',
  cyan: 'var(--player-cyan)',
  pink: 'var(--player-pink)',
  lime: 'var(--player-lime)',
  white: 'var(--player-white)',
};

export const PLAYER_COLOR_LABEL: Record<string, string> = {
  red: 'Rojo',
  blue: 'Azul',
  green: 'Verde',
  yellow: 'Amarillo',
  purple: 'Violeta',
  orange: 'Naranja',
  cyan: 'Celeste',
  pink: 'Rosa',
  lime: 'Lima',
  white: 'Blanco',
};

export const ALL_COLORS = Object.keys(COLOR_VALUES);
const NEUTRAL = '#a8a29e';

export function colorValue(color: string | null | undefined): string {
  if (!color) return NEUTRAL;
  return COLOR_VALUES[color] ?? color; // color desconocido: se usa tal cual (CSS color)
}

/** Orden de la paleta de Arte (p01..p06) → nombres de color que usa el backend. */
const PALETTE_ORDER = ['red', 'blue', 'green', 'yellow', 'orange', 'purple'];

/** Pisa las CSS variables --player-* con los hex de brand/palette/palette.json. */
export function applyPalette(palette: BrandPalette, root: HTMLElement = document.documentElement): void {
  palette.players.slice(0, PALETTE_ORDER.length).forEach((entry, i) => {
    root.style.setProperty(`--player-${PALETTE_ORDER[i]}`, entry.hex);
  });
}
