import { z } from 'zod';

export const PlayerRole = z.enum(['admin', 'player', 'spectator', 'ai_commentator', 'ai_player']);
export type PlayerRole = z.infer<typeof PlayerRole>;

export const Presence = z.enum(['online', 'reconnecting', 'offline']);
export type Presence = z.infer<typeof Presence>;

/** Shape base de jugador que emite el backend en snapshot y eventos. */
export const PublicPlayer = z.object({
  id: z.string(),
  nickname: z.string(),
  role: PlayerRole,
  color: z.string().nullable(),
  avatar_asset_id: z.string().nullable(),
  is_ready: z.boolean(),
  eliminated: z.boolean(),
  joined: z.boolean(),
  presence: Presence.optional(), // presente en snapshot y GET admin
  profile_id: z.string().nullable().optional(), // perfil persistente del grupo
});
export type PublicPlayer = z.infer<typeof PublicPlayer>;

/** Vista admin: agrega estado del token y editabilidad del apodo. */
export const AdminPlayer = PublicPlayer.extend({
  token_revoked: z.boolean(),
  nickname_editable: z.boolean(),
});
export type AdminPlayer = z.infer<typeof AdminPlayer>;

/** Forma ad-hoc del GET /api/join (preview): usa already_joined, sin is_ready/eliminated. */
export const JoinPreviewPlayer = z.object({
  id: z.string(),
  nickname: z.string(),
  role: PlayerRole,
  color: z.string().nullable(),
  nickname_editable: z.boolean(),
  already_joined: z.boolean(),
});
export type JoinPreviewPlayer = z.infer<typeof JoinPreviewPlayer>;
