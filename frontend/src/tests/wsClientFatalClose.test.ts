import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

// El bug: el backend agrego un tope de 3 conexiones simultaneas por jugador;
// al abrir una cuarta pestana desaloja la mas vieja con close code 4009 para
// que la reconexion desde otro dispositivo nunca falle. Pero el cliente no
// conocia ese codigo: la pestana desalojada reintentaba a los ~500ms,
// desalojando a la siguiente, que reintentaba, etc. Con 4 pestanas del mismo
// jugador quedaba un anillo estable de desalojos, cada uno con un
// game.snapshot completo (el payload pesado que esta fase vino a reducir).

vi.mock('../services/playtest/playtestClient', () => ({
  playtestClient: { track: vi.fn(), reportTechnical: vi.fn(), init: vi.fn() },
}));

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSING = 2;
  static readonly CLOSED = 3;
  onopen: (() => void) | null = null;
  onclose: ((event: { code: number; reason: string }) => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  readyState = FakeWebSocket.CONNECTING;
  constructor(public url: string) {
    FakeWebSocket.instances.push(this);
  }
  send(): void {}
  close(): void {}
}

// entorno de test vitest corre con `environment: 'node'`: no hay `location`
// ni `WebSocket` globales, así que se stubean acá antes de importar el cliente.
(globalThis as any).location = { protocol: 'http:', host: 'localhost' };

describe('wsClient: cierre 4009 (desalojo por tope de conexiones) no reintenta', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    FakeWebSocket.instances = [];
    (globalThis as any).WebSocket = FakeWebSocket;
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('un cierre con codigo 4009 deja el status en revoked y NO agenda reconexion', async () => {
    const { wsClient } = await import('../services/websocket/wsClient');
    wsClient.connect('ABCD', 'tok');
    expect(FakeWebSocket.instances).toHaveLength(1);

    FakeWebSocket.instances[0].onclose!({ code: 4009, reason: '' });

    expect(wsClient.status).toBe('revoked');

    // si el 4009 no estuviera en FATAL_CLOSE_CODES, esto abriria una segunda
    // conexion (el anillo de reconexion que este arreglo elimina)
    vi.advanceTimersByTime(30_000);
    expect(FakeWebSocket.instances).toHaveLength(1);

    wsClient.disconnect();
  });

  it('un cierre no fatal (1006, ej. corte de red) si agenda reconexion', async () => {
    const { wsClient } = await import('../services/websocket/wsClient');
    wsClient.connect('ABCD', 'tok');
    expect(FakeWebSocket.instances).toHaveLength(1);

    FakeWebSocket.instances[0].onclose!({ code: 1006, reason: '' });

    expect(wsClient.status).toBe('reconnecting');

    vi.advanceTimersByTime(30_000);
    expect(FakeWebSocket.instances.length).toBeGreaterThan(1);

    wsClient.disconnect();
  });
});
