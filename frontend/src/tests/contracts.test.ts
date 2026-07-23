import { describe, expect, it } from 'vitest';
import {
  GameEventEnvelope,
  EVENT_PAYLOAD_SCHEMAS,
  ClientMessage,
  SnapshotPayload,
  SCHEMA_VERSION,
} from '@teg/contracts';

const envelope = (over: Record<string, unknown> = {}) => ({
  event_id: '3f2b7c9e-0000-0000-0000-000000000000',
  event_type: 'chat.message',
  game_id: 'g1',
  actor_id: 'p1',
  target_id: null,
  timestamp: '2026-07-22T20:00:00+00:00',
  sequence_number: 7,
  payload: { text: 'hola' },
  visibility: 'public',
  schema_version: SCHEMA_VERSION,
  persisted: true,
  ...over,
});

describe('contratos del backend real', () => {
  it('valida el sobre de evento (event-envelope.schema.json)', () => {
    const parsed = GameEventEnvelope.parse(envelope());
    expect(parsed.sequence_number).toBe(7);
  });

  it('rechaza sobres sin campos obligatorios', () => {
    expect(GameEventEnvelope.safeParse({ event_type: 'x' }).success).toBe(false);
  });

  it('valida el payload del snapshot con turn null y con turn activo', () => {
    const base = {
      game: { id: 'g1', code: 'x7k3q9mw', name: 'la-revancha', status: 'lobby' },
      you: 'p1',
      players: [{
        id: 'p1', nickname: 'Nessi', role: 'player', color: 'red',
        avatar_asset_id: null, is_ready: true, eliminated: false, joined: true, presence: 'online',
      }],
      turn: null,
      recent_events: [],
    };
    expect(SnapshotPayload.safeParse(base).success).toBe(true);
    expect(SnapshotPayload.safeParse({ ...base, turn: { order: ['p1'], index: 0, turn_number: 3 } }).success).toBe(true);
  });

  it('valida payloads conocidos y rechaza los malformados', () => {
    expect(EVENT_PAYLOAD_SCHEMAS['dice.rolled'].safeParse({ dice: [6, 3, 1], count: 3 }).success).toBe(true);
    expect(EVENT_PAYLOAD_SCHEMAS['dice.rolled'].safeParse({ dice: 'seis' }).success).toBe(false);
    expect(EVENT_PAYLOAD_SCHEMAS['attack.resolved'].safeParse({
      attacker_dice: [6, 4], defender_dice: [6, 3], attacker_losses: 1, defender_losses: 1,
      comparisons: [{ attacker: 6, defender: 6 }, { attacker: 4, defender: 3 }],
    }).success).toBe(true);
    expect(EVENT_PAYLOAD_SCHEMAS['player.ready'].safeParse({ ready: true, all_ready: false, game_status: 'lobby' }).success).toBe(true);
  });

  it('mensajes cliente: formato {type, payload} del backend', () => {
    expect(ClientMessage.safeParse({ type: 'ready.set', payload: { ready: true } }).success).toBe(true);
    expect(ClientMessage.safeParse({ type: 'chat.send', payload: { text: 'hola' } }).success).toBe(true);
    expect(ClientMessage.safeParse({ type: 'dice.roll', payload: { count: 3 } }).success).toBe(true);
    expect(ClientMessage.safeParse({ type: 'attack', payload: { target_player_id: 'p2' } }).success).toBe(true);
    expect(ClientMessage.safeParse({ type: 'ping' }).success).toBe(true);
    expect(ClientMessage.safeParse({ type: 'hack.everything' }).success).toBe(false);
    expect(ClientMessage.safeParse({ type: 'dice.roll', payload: { count: 9 } }).success).toBe(false);
  });
});
