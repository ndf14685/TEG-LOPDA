import { describe, expect, it } from 'vitest';
import { SeqTracker } from '../services/websocket/seqTracker';

describe('SeqTracker', () => {
  it('acepta el primer seq persistido y los consecutivos', () => {
    const t = new SeqTracker();
    expect(t.accept(5)).toBe('ok');
    expect(t.accept(6)).toBe('ok');
    expect(t.accept(7)).toBe('ok');
  });

  it('los efímeros (seq 0) pasan sin afectar el stream', () => {
    const t = new SeqTracker();
    expect(t.accept(0)).toBe('ok');
    expect(t.accept(3)).toBe('ok');
    expect(t.accept(0)).toBe('ok'); // presence.changed, error, snapshot
    expect(t.accept(4)).toBe('ok');
  });

  it('detecta huecos (eventos perdidos)', () => {
    const t = new SeqTracker();
    t.accept(1);
    expect(t.accept(4)).toBe('gap');
    expect(t.current).toBe(1); // no avanza hasta resincronizar
  });

  it('descarta eventos viejos o duplicados', () => {
    const t = new SeqTracker();
    t.accept(10);
    expect(t.accept(10)).toBe('stale');
    expect(t.accept(3)).toBe('stale');
  });

  it('resetea al reconectar (el snapshot re-ancla)', () => {
    const t = new SeqTracker();
    t.accept(9);
    t.reset(null);
    expect(t.accept(42)).toBe('ok'); // primer persistido tras snapshot ancla
    expect(t.accept(43)).toBe('ok');
  });
});
