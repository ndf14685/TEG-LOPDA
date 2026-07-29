import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

// El bug: handleMessage retorna en el caso 'pong' ANTES de limpiar
// pendingTimers, asi que cada ping genera un incidente falso a los 8 s.
// Registrado como PLAY-001 con frecuencia 41 en data/playtest.db.

const reportTechnical = vi.fn();
vi.mock('../services/playtest/playtestClient', () => ({
  playtestClient: { track: vi.fn(), reportTechnical, init: vi.fn() },
}));

describe('wsClient: el pong resuelve el ping', () => {
  beforeEach(() => { vi.useFakeTimers(); reportTechnical.mockClear(); });
  afterEach(() => { vi.useRealTimers(); });

  it('no reporta accion pendiente cuando el server contesta pong', async () => {
    const { wsClient } = await import('../services/websocket/wsClient');
    const fake = { readyState: 1, send: vi.fn() };
    (wsClient as any).ws = fake;

    wsClient.send({ type: 'ping' } as any);
    (wsClient as any).handleMessage(JSON.stringify({ type: 'pong' }));
    vi.advanceTimersByTime(10_000);

    expect(reportTechnical).not.toHaveBeenCalled();
  });

  it('no arma el temporizador si el socket no esta abierto', async () => {
    const { wsClient } = await import('../services/websocket/wsClient');
    (wsClient as any).ws = { readyState: 3, send: vi.fn() }; // CLOSED

    wsClient.send({ type: 'ping' } as any);
    vi.advanceTimersByTime(10_000);

    expect(reportTechnical).not.toHaveBeenCalled();
  });

  it('un mensaje con JSON invalido tambien cancela el temporizador pendiente', async () => {
    const { wsClient } = await import('../services/websocket/wsClient');
    const fake = { readyState: 1, send: vi.fn() };
    (wsClient as any).ws = fake;

    wsClient.send({ type: 'ping' } as any);
    (wsClient as any).handleMessage('{ esto no es json valido');
    vi.advanceTimersByTime(10_000);

    // se reporta el JSON invalido, pero nunca el timeout de accion pendiente:
    // cualquier mensaje real del server, valido o no, prueba que la conexion
    // esta viva y cancela el temporizador.
    expect(reportTechnical).toHaveBeenCalledTimes(1);
    expect(reportTechnical).toHaveBeenCalledWith(
      expect.objectContaining({ error_type: 'websocket-json-parse' }),
    );
  });
});
