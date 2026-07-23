import { z } from 'zod';
import { SnapshotPayload, GameStatus, TurnState } from './game';
import { PublicPlayer, Presence } from './player';

/**
 * Sobre de todo evento servidor→cliente (event-envelope.schema.json).
 * sequence_number: monotónico ≥1 en eventos persistidos; 0 en efímeros
 * (game.snapshot, presence.changed, error).
 */
export const GameEventEnvelope = z.object({
  event_id: z.string(),
  event_type: z.string(),
  game_id: z.string(),
  actor_id: z.string().nullable().optional(),
  target_id: z.string().nullable().optional(),
  timestamp: z.string(),
  sequence_number: z.number().int(),
  payload: z.record(z.string(), z.unknown()),
  visibility: z.enum(['public', 'private', 'admin']),
  schema_version: z.string(),
  persisted: z.boolean().optional(),
});
export type GameEventEnvelope = z.infer<typeof GameEventEnvelope>;

/** Único mensaje server→cliente que NO es envelope: respuesta al ping. */
export const PongMessage = z.object({ type: z.literal('pong') });

// ---- payloads por event_type ----

export const PlayerJoinedPayload = z.object({ player: PublicPlayer });
export const PlayerReadyPayload = z.object({ ready: z.boolean(), all_ready: z.boolean(), game_status: GameStatus });
export const PresenceChangedPayload = z.object({ presence: Presence });
export const GameStartedPayload = z.object({ turn_order: z.array(z.string()), players: z.array(PublicPlayer) });
export const TurnStartedPayload = z.object({ turn_number: z.number().int() });
export const TurnEndedPayload = z.object({ turn_number: z.number().int() }).partial();
export const DiceRolledPayload = z.object({ dice: z.array(z.number().int()), count: z.number().int() });
export const AttackResolvedPayload = z.object({
  attacker_dice: z.array(z.number().int()),
  defender_dice: z.array(z.number().int()),
  attacker_losses: z.number().int(),
  defender_losses: z.number().int(),
  comparisons: z.array(z.object({ attacker: z.number().int(), defender: z.number().int() })),
});
export const ChatMessagePayload = z.object({ text: z.string() });
export const TauntTriggeredPayload = z.object({
  audio_asset_id: z.string(),
  source_event_type: z.string(),
  source_event_id: z.string().nullable().optional(),
});
export const AICommentGeneratedPayload = z.object({
  text: z.string(),
  emotion: z.string().default('neutral'),
  audio_asset: z.string().nullable().default(null),
});
export const GameFinishedPayload = z.object({
  turns_played: z.number().int(),
  winner_player_id: z.string().nullable(),
  total_events: z.number().int(),
});
export const ErrorPayload = z.object({ code: z.string(), message: z.string() });

/**
 * Mapa event_type→schema de payload. El cliente valida contra esto y descarta
 * lo inválido. Eventos sin entrada se aceptan con payload opaco (forward-compat).
 */
export const EVENT_PAYLOAD_SCHEMAS = {
  'game.snapshot': SnapshotPayload,
  'player.joined': PlayerJoinedPayload,
  'player.ready': PlayerReadyPayload,
  'presence.changed': PresenceChangedPayload,
  'game.started': GameStartedPayload,
  'turn.started': TurnStartedPayload,
  'turn.ended': TurnEndedPayload,
  'dice.rolled': DiceRolledPayload,
  'attack.resolved': AttackResolvedPayload,
  'chat.message': ChatMessagePayload,
  'taunt.triggered': TauntTriggeredPayload,
  'ai.comment.generated': AICommentGeneratedPayload,
  'game.finished': GameFinishedPayload,
  'error': ErrorPayload,
} as const;
export type KnownEventType = keyof typeof EVENT_PAYLOAD_SCHEMAS;

/** Mensajes cliente→servidor (client-messages.schema.json). Máximo 8 KiB. */
export const ClientMessage = z.discriminatedUnion('type', [
  z.object({ type: z.literal('ping'), payload: z.object({}).optional() }),
  z.object({ type: z.literal('ready.set'), payload: z.object({ ready: z.boolean() }) }),
  z.object({
    type: z.literal('chat.send'),
    payload: z.object({ text: z.string().min(1).max(500), target_player_id: z.string().nullable().optional() }),
  }),
  z.object({ type: z.literal('dice.roll'), payload: z.object({ count: z.number().int().min(1).max(3) }) }),
  z.object({
    type: z.literal('attack'),
    payload: z.object({ target_player_id: z.string(), attacker_dice: z.number().int().min(1).max(3).optional() }),
  }),
  z.object({ type: z.literal('turn.end'), payload: z.object({}).optional() }),
  z.object({
    type: z.literal('turn.place_reinforcement'),
    payload: z.object({ territory_id: z.string(), count: z.number().int().min(1).default(1) }),
  }),
  z.object({
    type: z.literal('turn.fortify'),
    payload: z.object({
      source_territory_id: z.string(),
      target_territory_id: z.string(),
      count: z.number().int().min(1),
    }),
  }),
  z.object({ type: z.literal('turn.next_phase'), payload: z.object({}).optional() }),
  z.object({
    type: z.literal('cards.trade'),
    payload: z.object({ card_ids: z.array(z.string()).length(3) }),
  }),
]);
export type ClientMessage = z.infer<typeof ClientMessage>;
