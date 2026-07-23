import { z } from 'zod';
import { PlayerColor, PlayerProfile, PlayerRole } from './player';
import { GameSettings } from './game';

export const HealthResponse = z.object({
  ok: z.boolean(),
  protocolVersion: z.string(),
  uptimeSeconds: z.number(),
});
export type HealthResponse = z.infer<typeof HealthResponse>;

export const CreateGameRequest = z.object({
  gameName: z.string().min(1).max(60),
  admin: z.object({
    name: z.string().min(1).max(60),
    nickname: z.string().min(1).max(40),
    color: PlayerColor,
    avatarId: z.string(),
  }),
  settings: GameSettings.partial().optional(),
});
export type CreateGameRequest = z.infer<typeof CreateGameRequest>;

export const CreateGameResponse = z.object({
  gameId: z.string(),
  adminToken: z.string(),
  adminPlayerId: z.string(),
});
export type CreateGameResponse = z.infer<typeof CreateGameResponse>;

export const CreatePlayerRequest = z.object({
  profile: PlayerProfile,
  role: PlayerRole.default('player'),
});
export type CreatePlayerRequest = z.infer<typeof CreatePlayerRequest>;

export const PlayerLink = z.object({
  playerId: z.string(),
  token: z.string(),
  joinPath: z.string(), // "/join/:gameId/:token"
  revoked: z.boolean(),
});
export type PlayerLink = z.infer<typeof PlayerLink>;

export const CreatePlayerResponse = PlayerLink;

export const AdminGameView = z.object({
  gameId: z.string(),
  gameName: z.string(),
  links: z.array(
    PlayerLink.extend({
      profile: PlayerProfile,
      role: PlayerRole,
    }),
  ),
});
export type AdminGameView = z.infer<typeof AdminGameView>;

export const SessionRequest = z.object({ token: z.string() });
export const SessionResponse = z.object({
  sessionId: z.string(),
  gameId: z.string(),
  playerId: z.string(),
  role: PlayerRole,
  profile: PlayerProfile,
  protocolVersion: z.string(),
});
export type SessionResponse = z.infer<typeof SessionResponse>;

export const ConfirmNicknameRequest = z.object({ nickname: z.string().min(1).max(40) });
