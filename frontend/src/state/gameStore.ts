import { create } from 'zustand';
import type { GameSnapshot, PlayerPublic, AIComment } from '@teg/contracts';
import { z } from 'zod';
import { LobbyStatePayload, ChatMessagePayload, TauntTriggeredPayload } from '@teg/contracts';

export type LobbyState = z.infer<typeof LobbyStatePayload>;
export type ChatMessage = z.infer<typeof ChatMessagePayload>;
export type TauntEvent = z.infer<typeof TauntTriggeredPayload> & { receivedAt: number };

interface GameState {
  lobby: LobbyState | null;
  snapshot: GameSnapshot | null;
  chat: ChatMessage[];
  countdownMs: number | null;
  aiTyping: boolean;
  aiComments: AIComment[];
  aiMuted: boolean;
  lastTaunt: TauntEvent | null;
  selectedTerritoryId: string | null;

  applyLobby: (lobby: LobbyState) => void;
  applySnapshot: (snapshot: GameSnapshot) => void;
  addChat: (msg: ChatMessage) => void;
  setCountdown: (ms: number | null) => void;
  setAiTyping: (typing: boolean) => void;
  addAiComment: (comment: AIComment) => void;
  setAiMuted: (muted: boolean) => void;
  setTaunt: (taunt: TauntEvent | null) => void;
  selectTerritory: (id: string | null) => void;

  playerById: (id: string | null | undefined) => PlayerPublic | undefined;
}

export const useGameStore = create<GameState>((set, get) => ({
  lobby: null,
  snapshot: null,
  chat: [],
  countdownMs: null,
  aiTyping: false,
  aiComments: [],
  aiMuted: false,
  lastTaunt: null,
  selectedTerritoryId: null,

  applyLobby: (lobby) => set({ lobby }),
  applySnapshot: (snapshot) => set({ snapshot }),
  addChat: (msg) => set((s) => ({ chat: [...s.chat.slice(-99), msg] })),
  setCountdown: (countdownMs) => set({ countdownMs }),
  setAiTyping: (aiTyping) => set({ aiTyping }),
  addAiComment: (comment) => set((s) => ({ aiComments: [...s.aiComments.slice(-4), comment], aiTyping: false })),
  setAiMuted: (aiMuted) => set({ aiMuted }),
  setTaunt: (lastTaunt) => set({ lastTaunt }),
  selectTerritory: (selectedTerritoryId) => set({ selectedTerritoryId }),

  playerById: (id) => {
    if (!id) return undefined;
    const { snapshot, lobby } = get();
    return snapshot?.players.find((p) => p.id === id) ?? lobby?.players.find((p) => p.id === id);
  },
}));
