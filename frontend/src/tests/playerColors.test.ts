import { describe, expect, it } from 'vitest';
import { ALL_COLORS, PLAYER_COLOR_LABEL, colorValue } from '../utils/playerColors';

describe('paleta de jugadores', () => {
  it('incluye al menos 8 colores con los nuevos agregados', () => {
    expect(ALL_COLORS.length).toBeGreaterThanOrEqual(8);
    for (const c of ['cyan', 'pink', 'lime', 'white']) {
      expect(ALL_COLORS).toContain(c);
    }
  });

  it('cada color tiene etiqueta y valor CSS var', () => {
    for (const c of ALL_COLORS) {
      expect(PLAYER_COLOR_LABEL[c]).toBeTruthy();
      expect(colorValue(c)).toBe(`var(--player-${c})`);
    }
  });

  it('color desconocido cae al valor tal cual y nulo al neutral', () => {
    expect(colorValue('#123456')).toBe('#123456');
    expect(colorValue(null)).toBe('#a8a29e');
  });
});
