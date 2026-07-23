import { nanoid } from 'nanoid';
import type { GameSnapshot, GameSettings, PlayerProfile, PlayerPublic, PlayerRole, TerritoryState } from '@teg/contracts';
import { SLICE_MAP } from '@teg/contracts';

export interface PlayerRecord {
  id: string;
  role: PlayerRole;
  profile: PlayerProfile;
  token: string;
  revoked: boolean;
  ready: boolean;
  connected: boolean;
  everJoined: boolean;
  muted: boolean;
  lastTauntAt: number;
}

export interface GameRecord {
  id: string;
  name: string;
  status: 'lobby' | 'starting' | 'in-game' | 'paused' | 'finished';
  settings: GameSettings;
  players: Map<string, PlayerRecord>;
  territories: TerritoryState[];
  currentPlayerId: string | null;
  seq: number;
  createdAt: number;
}

export const games = new Map<string, GameRecord>();
export const sessions = new Map<string, { gameId: string; playerId: string }>();

export function createGame(name: string, settings: GameSettings): GameRecord {
  const game: GameRecord = {
    id: `partida-${nanoid(8).toLowerCase()}`,
    name,
    status: 'lobby',
    settings,
    players: new Map(),
    territories: [],
    currentPlayerId: null,
    seq: 0,
    createdAt: Date.now(),
  };
  games.set(game.id, game);
  return game;
}

export function createPlayer(game: GameRecord, profile: PlayerProfile, role: PlayerRole): PlayerRecord {
  const player: PlayerRecord = {
    id: `p-${nanoid(10)}`,
    role,
    profile,
    token: nanoid(24),
    revoked: false,
    ready: role === 'admin',
    connected: false,
    everJoined: false,
    muted: false,
    lastTauntAt: 0,
  };
  game.players.set(player.id, player);
  return player;
}

export function findByToken(token: string): { game: GameRecord; player: PlayerRecord } | null {
  for (const game of games.values()) {
    for (const player of game.players.values()) {
      if (player.token === token) return { game, player };
    }
  }
  return null;
}

export function publicPlayer(p: PlayerRecord): PlayerPublic {
  return {
    id: p.id,
    role: p.role,
    nickname: p.profile.nickname,
    color: p.profile.color,
    avatarId: p.profile.avatarId,
    titles: p.profile.titles,
    connection: p.connected ? 'connected' : p.everJoined ? 'disconnected' : 'never-joined',
    ready: p.ready,
    isAI: p.role === 'ai-player',
    muted: p.muted,
  };
}

/** Reparte los 8 territorios del slice round-robin entre jugadores no espectadores. */
export function dealTerritories(game: GameRecord): void {
  const combatants = [...game.players.values()].filter((p) => p.role === 'admin' || p.role === 'player' || p.role === 'ai-player');
  game.territories = SLICE_MAP.map((t, i) => ({
    id: t.id,
    continent: t.continent,
    ownerId: combatants[i % combatants.length]?.id ?? null,
    armies: 3,
  }));
  game.currentPlayerId = combatants[0]?.id ?? null;
}

export function snapshot(game: GameRecord): GameSnapshot {
  return {
    gameId: game.id,
    name: game.name,
    status: game.status,
    settings: game.settings,
    players: [...game.players.values()].map(publicPlayer),
    territories: game.territories,
    currentPlayerId: game.currentPlayerId,
    phase: game.status === 'in-game' ? 'deploy' : 'none',
    seq: game.seq,
  };
}
