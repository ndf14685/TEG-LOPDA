import type { PlayerColor } from '@teg/contracts';

export const PLAYER_COLOR_VAR: Record<PlayerColor, string> = {
  red: 'var(--player-red)',
  blue: 'var(--player-blue)',
  green: 'var(--player-green)',
  yellow: 'var(--player-yellow)',
  purple: 'var(--player-purple)',
  orange: 'var(--player-orange)',
};

export const PLAYER_COLOR_LABEL: Record<PlayerColor, string> = {
  red: 'Rojo',
  blue: 'Azul',
  green: 'Verde',
  yellow: 'Amarillo',
  purple: 'Violeta',
  orange: 'Naranja',
};

export const ALL_COLORS = Object.keys(PLAYER_COLOR_VAR) as PlayerColor[];
