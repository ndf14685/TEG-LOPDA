import { create } from 'zustand';
import type { GameRef, PublicPlayer, TurnState, AICommentView } from '@teg/contracts';

export interface ChatEntry {
  id: string;
  playerId: string | null;
  text: string;
  private: boolean;
  ts: string;
}

export interface DiceResult {
  playerId: string | null;
  dice: number[];
  ts: string;
}

export interface AttackResult {
  attackerId: string | null;
  defenderId: string | null;
  attackerDice: number[];
  defenderDice: number[];
  attackerLosses: number;
  defenderLosses: number;
  ts: string;
}

export interface TauntView {
  fromPlayerId: string | null;
  toPlayerId: string | null;
  audioAssetId: string;
  sourceEventType: string;
  receivedAt: number;
}

interface GameState {
  game: GameRef | null;
  youId: string | null;
  players: PublicPlayer[];
  turn: TurnState | null;
  chat: ChatEntry[];
  lastDice: DiceResult | null;
  lastAttack: AttackResult | null;
  aiComments: AICommentView[];
  aiMuted: boolean;
  lastTaunt: TauntView | null;
  gameStartedAt: number | null;
  finished: { winnerPlayerId: string | null; turnsPlayed: number } | null;
  lastError: { code: string; message: string; at: number } | null;

  applySnapshot: (game: GameRef, youId: string, players: PublicPlayer[], turn: TurnState | null) => void;
  upsertPlayer: (player: PublicPlayer) => void;
  patchPlayer: (id: string, patch: Partial<PublicPlayer>) => void;
  setGameStatus: (status: GameRef['status']) => void;
  setTurn: (turn: TurnState | null) => void;
  addChat: (entry: ChatEntry) => void;
  setDice: (dice: DiceResult) => void;
  setAttack: (attack: AttackResult) => void;
  addAiComment: (comment: AICommentView) => void;
  setAiMuted: (muted: boolean) => void;
  setTaunt: (taunt: TauntView | null) => void;
  markStarted: () => void;
  setFinished: (winnerPlayerId: string | null, turnsPlayed: number) => void;
  setError: (code: string, message: string) => void;

  playerById: (id: string | null | undefined) => PublicPlayer | undefined;
  currentPlayerId: () => string | null;
}

export const useGameStore = create<GameState>((set, get) => ({
  game: null,
  youId: null,
  players: [],
  turn: null,
  chat: [],
  lastDice: null,
  lastAttack: null,
  aiComments: [],
  aiMuted: false,
  lastTaunt: null,
  gameStartedAt: null,
  finished: null,
  lastError: null,

  applySnapshot: (game, youId, players, turn) => set({ game, youId, players, turn }),

  upsertPlayer: (player) =>
    set((s) => {
      const idx = s.players.findIndex((p) => p.id === player.id);
      const players = [...s.players];
      if (idx >= 0) players[idx] = { ...players[idx], ...player };
      else players.push(player);
      return { players };
    }),

  patchPlayer: (id, patch) =>
    set((s) => ({ players: s.players.map((p) => (p.id === id ? { ...p, ...patch } : p)) })),

  setGameStatus: (status) => set((s) => (s.game ? { game: { ...s.game, status } } : {})),
  setTurn: (turn) => set({ turn }),
  addChat: (entry) => set((s) => ({ chat: [...s.chat.slice(-99), entry] })),
  setDice: (lastDice) => set({ lastDice }),
  setAttack: (lastAttack) => set({ lastAttack }),
  addAiComment: (comment) => set((s) => ({ aiComments: [...s.aiComments.slice(-4), comment] })),
  setAiMuted: (aiMuted) => set({ aiMuted }),
  setTaunt: (lastTaunt) => set({ lastTaunt }),
  markStarted: () => set({ gameStartedAt: Date.now() }),
  setFinished: (winnerPlayerId, turnsPlayed) => set({ finished: { winnerPlayerId, turnsPlayed } }),
  setError: (code, message) => set({ lastError: { code, message, at: Date.now() } }),

  playerById: (id) => (id ? get().players.find((p) => p.id === id) : undefined),
  currentPlayerId: () => {
    const { turn } = get();
    if (!turn || turn.order.length === 0) return null;
    return turn.order[turn.index % turn.order.length] ?? null;
  },
}));
