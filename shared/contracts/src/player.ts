import { z } from 'zod';

export const PlayerRole = z.enum(['admin', 'player', 'spectator', 'ai-player']);
export type PlayerRole = z.infer<typeof PlayerRole>;

export const PlayerColor = z.enum(['red', 'blue', 'green', 'yellow', 'purple', 'orange']);
export type PlayerColor = z.infer<typeof PlayerColor>;

export const ConnectionState = z.enum(['connected', 'disconnected', 'never-joined']);
export type ConnectionState = z.infer<typeof ConnectionState>;

/** Datos que el admin precarga por jugador. Nunca viajan en la URL. */
export const PlayerProfile = z.object({
  name: z.string().min(1).max(60),
  nickname: z.string().min(1).max(40),
  color: PlayerColor,
  avatarId: z.string(), // id dot-notation del asset manifest
  tauntAudioIds: z.array(z.string()).default([]),
  trustLevel: z.number().int().min(0).max(10).default(5),
  titles: z.array(z.string()).default([]),
  relationships: z.record(z.string(), z.string()).default({}),
});
export type PlayerProfile = z.infer<typeof PlayerProfile>;

/** Vista pública de un jugador (lo que ven los demás). */
export const PlayerPublic = z.object({
  id: z.string(),
  role: PlayerRole,
  nickname: z.string(),
  color: PlayerColor,
  avatarId: z.string(),
  titles: z.array(z.string()),
  connection: ConnectionState,
  ready: z.boolean(),
  isAI: z.boolean().default(false),
  muted: z.boolean().default(false),
});
export type PlayerPublic = z.infer<typeof PlayerPublic>;
