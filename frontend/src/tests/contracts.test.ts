import { describe, expect, it } from 'vitest';
import { ServerEnvelope, SERVER_EVENT_SCHEMAS, ClientMessage, GameSnapshot, SLICE_MAP } from '@teg/contracts';

describe('contratos compartidos', () => {
  it('valida un sobre de evento correcto', () => {
    const env = ServerEnvelope.parse({ v: '0.1.0', seq: 1, type: 'lobby.state', ts: Date.now(), payload: {} });
    expect(env.seq).toBe(1);
  });

  it('rechaza payloads inválidos de lobby.state', () => {
    const result = SERVER_EVENT_SCHEMAS['lobby.state'].safeParse({ gameId: 1 });
    expect(result.success).toBe(false);
  });

  it('valida mensajes de cliente y rechaza tipos desconocidos', () => {
    expect(ClientMessage.safeParse({ type: 'player.ready', ready: true }).success).toBe(true);
    expect(ClientMessage.safeParse({ type: 'hack.everything' }).success).toBe(false);
  });

  it('el mapa del slice tiene fronteras simétricas', () => {
    const byId = new Map(SLICE_MAP.map((t) => [t.id, t]));
    for (const t of SLICE_MAP) {
      for (const border of t.borders) {
        expect(byId.get(border)?.borders, `${border} debe listar a ${t.id}`).toContain(t.id);
      }
    }
  });

  it('un snapshot completo pasa el schema', () => {
    const snapshot = {
      gameId: 'g1', name: 'test', status: 'in-game', settings: { aiCommentatorEnabled: true, humorLevel: 2 },
      players: [], territories: SLICE_MAP.map((t) => ({ id: t.id, continent: t.continent, ownerId: null, armies: 3 })),
      currentPlayerId: null, phase: 'deploy', seq: 10,
    };
    expect(GameSnapshot.safeParse(snapshot).success).toBe(true);
  });
});
