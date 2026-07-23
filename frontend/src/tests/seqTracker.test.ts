import { describe, expect, it } from 'vitest';
import { SeqTracker } from '../services/websocket/seqTracker';

describe('SeqTracker', () => {
  it('acepta el primer seq y los consecutivos', () => {
    const t = new SeqTracker();
    expect(t.accept(5)).toBe('ok');
    expect(t.accept(6)).toBe('ok');
    expect(t.accept(7)).toBe('ok');
  });

  it('detecta huecos (eventos perdidos)', () => {
    const t = new SeqTracker();
    t.accept(1);
    expect(t.accept(4)).toBe('gap');
    // no avanza hasta resincronizar
    expect(t.current).toBe(1);
  });

  it('descarta eventos viejos o duplicados', () => {
    const t = new SeqTracker();
    t.accept(10);
    expect(t.accept(10)).toBe('stale');
    expect(t.accept(3)).toBe('stale');
  });

  it('resetea con snapshot', () => {
    const t = new SeqTracker();
    t.accept(1);
    t.reset(20);
    expect(t.accept(21)).toBe('ok');
  });
});
