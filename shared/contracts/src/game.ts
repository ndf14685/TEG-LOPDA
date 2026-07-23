import { z } from 'zod';
import { PlayerPublic } from './player';
import { TerritoryState } from './map';

export const GameStatus = z.enum(['lobby', 'starting', 'in-game', 'paused', 'finished']);
export type GameStatus = z.infer<typeof GameStatus>;

export const GamePhase = z.enum(['deploy', 'attack', 'fortify', 'none']);
export type GamePhase = z.infer<typeof GamePhase>;

export const GameSettings = z.object({
  aiCommentatorEnabled: z.boolean().default(true),
  humorLevel: z.number().int().min(0).max(3).default(2),
});
export type GameSettings = z.infer<typeof GameSettings>;

/** Snapshot completo del estado visible: lo único que el frontend acepta como verdad. */
export const GameSnapshot = z.object({
  gameId: z.string(),
  name: z.string(),
  status: GameStatus,
  settings: GameSettings,
  players: z.array(PlayerPublic),
  territories: z.array(TerritoryState),
  currentPlayerId: z.string().nullable(),
  phase: GamePhase,
  seq: z.number().int(),
});
export type GameSnapshot = z.infer<typeof GameSnapshot>;
