import { z } from 'zod';
import { GameSnapshot } from './game';
import { PlayerPublic } from './player';
import { AIComment } from './ai';

/** Sobre común de todo evento servidor→cliente. seq es por partida, monotónico. */
export const ServerEnvelope = z.object({
  v: z.string(),
  seq: z.number().int(),
  type: z.string(),
  ts: z.number(),
  payload: z.unknown(),
});
export type ServerEnvelope = z.infer<typeof ServerEnvelope>;

export const LobbyStatePayload = z.object({
  gameId: z.string(),
  gameName: z.string(),
  status: z.enum(['lobby', 'starting', 'in-game', 'paused', 'finished']),
  players: z.array(PlayerPublic),
});

export const ChatMessagePayload = z.object({
  playerId: z.string(),
  text: z.string().max(300),
  ts: z.number(),
});

export const GameStartingPayload = z.object({ countdownMs: z.number() });
export const GameStartedPayload = z.object({ snapshot: GameSnapshot });
export const SnapshotPayload = z.object({ snapshot: GameSnapshot });

export const TauntTriggeredPayload = z.object({
  fromPlayerId: z.string(),
  soundboardId: z.string(),
  text: z.string(),
  audioAssetId: z.string().nullable(),
});

export const AICommentTypingPayload = z.object({ commentId: z.string() });
export const AICommentGeneratedPayload = z.object({ comment: AIComment });
export const AICommentCancelledPayload = z.object({ commentId: z.string() });
export const AICommentErrorPayload = z.object({ commentId: z.string(), message: z.string() });

export const ErrorPayload = z.object({ code: z.string(), message: z.string() });

/** Mapa tipo→schema. El cliente valida payloads contra esto y descarta lo inválido. */
export const SERVER_EVENT_SCHEMAS = {
  'lobby.state': LobbyStatePayload,
  'chat.message': ChatMessagePayload,
  'game.starting': GameStartingPayload,
  'game.started': GameStartedPayload,
  'game.snapshot': SnapshotPayload,
  'taunt.triggered': TauntTriggeredPayload,
  'ai.comment.typing': AICommentTypingPayload,
  'ai.comment.generated': AICommentGeneratedPayload,
  'ai.comment.cancelled': AICommentCancelledPayload,
  'ai.comment.error': AICommentErrorPayload,
  'error': ErrorPayload,
} as const;
export type ServerEventType = keyof typeof SERVER_EVENT_SCHEMAS;

/** Mensajes cliente→servidor. */
export const ClientMessage = z.discriminatedUnion('type', [
  z.object({ type: z.literal('player.ready'), ready: z.boolean() }),
  z.object({ type: z.literal('chat.send'), text: z.string().min(1).max(300) }),
  z.object({ type: z.literal('game.start') }),
  z.object({ type: z.literal('sync.request') }),
  z.object({ type: z.literal('taunt.trigger'), soundboardId: z.string() }),
]);
export type ClientMessage = z.infer<typeof ClientMessage>;
