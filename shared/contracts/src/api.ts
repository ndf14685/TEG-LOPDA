import { z } from 'zod';
import { AdminGame, GameRef } from './game';
import { AdminPlayer, JoinPreviewPlayer, PublicPlayer, PlayerRole } from './player';
import { GameEventEnvelope } from './ws-events';

// ---- Público ----

export const HealthResponse = z.object({ status: z.string(), version: z.string() });
export type HealthResponse = z.infer<typeof HealthResponse>;

/** GET /api/join/{code}/{token} — resuelve el link sin unirse. */
export const JoinPreviewResponse = z.object({
  game: GameRef,
  player: JoinPreviewPlayer,
});
export type JoinPreviewResponse = z.infer<typeof JoinPreviewResponse>;

/** POST /api/join/{code}/{token} — confirma ingreso. ws_path NO incluye el token. */
export const JoinConfirmRequest = z.object({ nickname: z.string().max(64).nullable().optional() });
export const JoinConfirmResponse = z.object({
  game: GameRef,
  player: PublicPlayer.extend({ nickname_editable: z.boolean() }),
  ws_path: z.string(),
});
export type JoinConfirmResponse = z.infer<typeof JoinConfirmResponse>;

// ---- Admin (header X-Admin-Token) ----

export const CreateGameRequest = z.object({
  name: z.string().min(1).max(60),
  config: z.record(z.string(), z.unknown()).optional(),
});
export type CreateGameRequest = z.infer<typeof CreateGameRequest>;
export const CreateGameResponse = z.object({
  game: AdminGame,
  lobby_url: z.string(), // /join/{code} sin token: landing de la sala
});
export type CreateGameResponse = z.infer<typeof CreateGameResponse>;

export const AdminGameDetailResponse = z.object({
  game: AdminGame,
  players: z.array(AdminPlayer),
});
export type AdminGameDetailResponse = z.infer<typeof AdminGameDetailResponse>;

export const InvitePlayerRequest = z.object({
  nickname: z.string().min(1).max(64),
  role: PlayerRole.optional(),
  color: z.string().max(16).nullable().optional(),
  nickname_editable: z.boolean().nullable().optional(),
});
export type InvitePlayerRequest = z.infer<typeof InvitePlayerRequest>;
/** El token en claro aparece SOLO acá (o en regenerate). ai_player: token y join_url null. */
export const InvitePlayerResponse = z.object({
  player: AdminPlayer,
  token: z.string().nullable(),
  join_url: z.string().nullable(),
});
export type InvitePlayerResponse = z.infer<typeof InvitePlayerResponse>;

export const RegenerateTokenResponse = z.object({ token: z.string(), join_url: z.string() });
export const StartGameResponse = z.object({ status: z.string(), turn_order: z.array(z.string()) });
export const OkResponse = z.object({ ok: z.boolean() });
export const EventsResponse = z.object({ events: z.array(GameEventEnvelope) });

export const CommentatorConfigRequest = z.object({
  enabled: z.boolean().optional(),
  humor_level: z.number().int().min(0).max(4).optional(),
  muted: z.boolean().optional(),
});
export type CommentatorConfigRequest = z.infer<typeof CommentatorConfigRequest>;
