import { create } from 'zustand';
import type {
  GameRef, PublicPlayer, TurnState, AICommentView, CountryCard, SecretObjective, GameStage,
} from '@teg/contracts';

export interface LegalAction {
  action: string;
  params: Record<string, unknown>;
}

export interface BattleRound {
  attackerDice: number[];
  defenderDice: number[];
  attackerLosses: number;
  defenderLosses: number;
  comparisons: { attacker: number; defender: number }[];
  attackerAfter: number | null;
  defenderAfter: number | null;
}

/** Batalla acumulada para la Arena de Combate: se reconstruye de eventos. */
export interface BattleState {
  sourceId: string;
  targetId: string;
  attackerId: string | null;
  defenderId: string | null;
  attackerInitial: number;
  defenderInitial: number;
  rounds: BattleRound[];
  conquered: boolean;
  open: boolean;
}

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

export interface TerritoryStateData {
  id: string;
  owner_player_id: string | null;
  armies: number;
}

interface GameState {
  game: GameRef | null;
  youId: string | null;
  players: PublicPlayer[];
  turn: TurnState | null;
  territories: Record<string, TerritoryStateData>;
  cards: CountryCard[];
  secretObjective: SecretObjective | null;
  stage: GameStage | null;
  placementRemaining: number;
  placementPending: Record<string, number>;
  placementDone: string[];
  reinforceBatch: number;
  legalActions: LegalAction[];
  finishedObjective: SecretObjective | null;
  pacts: string[][];
  pactProposalFrom: string | null;
  conquestFlash: { territoryId: string; ts: number } | null;
  trophies: Record<string, { id: string; title: string; icon: string; blurb: string; value: string }[]> | null;
  radialMenu: { territoryId: string; x: number; y: number } | null;
  targetingMode: 'attack' | 'fortify' | null;
  fortifyPicker: { source: string; target: string } | null;
  battle: BattleState | null;
  mapAdjacency: Record<string, string[]>;
  selectedSourceTerritory: string | null;
  selectedTargetTerritory: string | null;
  chat: ChatEntry[];
  lastDice: DiceResult | null;
  lastAttack: AttackResult | null;
  lastReaction: { id: number; emoji: string; fromPlayerId: string | null } | null;
  lastWager: { id: number; playerId: string | null; won: boolean; wagered: number; payout: number } | null;
  aiComments: AICommentView[];
  aiMuted: boolean;
  soundsMuted: boolean;
  lastTaunt: TauntView | null;
  gameStartedAt: number | null;
  finished: { winnerPlayerId: string | null; turnsPlayed: number } | null;
  lastError: { code: string; message: string; at: number } | null;

  applySnapshot: (
    game: GameRef,
    youId: string,
    players: PublicPlayer[],
    turn: TurnState | null,
    territories?: Record<string, TerritoryStateData>,
    mapAdjacency?: Record<string, string[]>
  ) => void;
  upsertPlayer: (player: PublicPlayer) => void;
  patchPlayer: (id: string, patch: Partial<PublicPlayer>) => void;
  setGameStatus: (status: GameRef['status']) => void;
  setTurn: (turn: TurnState | null) => void;
  setTerritories: (territories: Record<string, TerritoryStateData>) => void;
  setCards: (cards: CountryCard[]) => void;
  setSecretObjective: (objective: SecretObjective | null) => void;
  setStage: (stage: GameStage | null) => void;
  setPlacement: (remaining: number, pending: Record<string, number>) => void;
  optimisticPlace: (territoryId: string) => void;
  setPlacementDone: (players: string[]) => void;
  setReinforceBatch: (n: number) => void;
  setLegalActions: (actions: LegalAction[]) => void;
  setFinishedObjective: (objective: SecretObjective | null) => void;
  setPacts: (pacts: string[][]) => void;
  addPact: (pact: string[]) => void;
  removePact: (pact: string[]) => void;
  setPactProposalFrom: (playerId: string | null) => void;
  setConquestFlash: (territoryId: string) => void;
  setTrophies: (trophies: Record<string, { id: string; title: string; icon: string; blurb: string; value: string }[]>) => void;
  setRadialMenu: (menu: { territoryId: string; x: number; y: number } | null) => void;
  setTargetingMode: (mode: 'attack' | 'fortify' | null) => void;
  setFortifyPicker: (picker: { source: string; target: string } | null) => void;
  startBattleRound: (round: BattleRound, ctx: {
    sourceId: string; targetId: string; attackerId: string | null; defenderId: string | null;
    attackerBefore: number; defenderBefore: number;
  }) => void;
  markBattleConquered: (territoryId: string) => void;
  closeBattle: () => void;
  hasPactWith: (playerId: string | null | undefined) => boolean;
  updateTerritory: (territory: TerritoryStateData) => void;
  setSelectedSourceTerritory: (tid: string | null) => void;
  setSelectedTargetTerritory: (tid: string | null) => void;
  addChat: (entry: ChatEntry) => void;
  setDice: (dice: DiceResult) => void;
  setAttack: (attack: AttackResult) => void;
  pushReaction: (emoji: string, fromPlayerId: string | null) => void;
  pushWagerResult: (playerId: string | null, won: boolean, wagered: number, payout: number) => void;
  addAiComment: (comment: AICommentView) => void;
  setAiMuted: (muted: boolean) => void;
  setSoundsMuted: (muted: boolean) => void;
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
  territories: {},
  cards: [],
  secretObjective: null,
  stage: null,
  placementRemaining: 0,
  placementPending: {},
  placementDone: [],
  reinforceBatch: 1,
  legalActions: [],
  finishedObjective: null,
  pacts: [],
  pactProposalFrom: null,
  conquestFlash: null,
  trophies: null,
  radialMenu: null,
  targetingMode: null,
  fortifyPicker: null,
  battle: null,
  mapAdjacency: {},
  selectedSourceTerritory: null,
  selectedTargetTerritory: null,
  chat: [],
  lastDice: null,
  lastAttack: null,
  lastReaction: null,
  lastWager: null,
  aiComments: [],
  aiMuted: true, // comentarista silenciado por default; se activa desde el panel
  soundsMuted: true, // sonidos silenciados por default; toggle en el juego
  lastTaunt: null,
  gameStartedAt: null,
  finished: null,
  lastError: null,

  applySnapshot: (game, youId, players, turn, territories, mapAdjacency) =>
    set({
      game, youId, players, turn,
      territories: territories ?? get().territories,
      mapAdjacency: mapAdjacency ?? get().mapAdjacency,
    }),

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
  setTerritories: (territories) => set({ territories }),
  setCards: (cards) => set({ cards }),
  setSecretObjective: (secretObjective) => set({ secretObjective }),
  setStage: (stage) => set({ stage }),
  setPlacement: (placementRemaining, placementPending) =>
    set({ placementRemaining, placementPending }),
  // eco optimista de un click de colocación: mueve el contador al instante.
  // El server responde placement.updated y reescribe con la verdad autoritativa.
  optimisticPlace: (territoryId) =>
    set((s) =>
      s.placementRemaining <= 0
        ? {}
        : {
            placementRemaining: s.placementRemaining - 1,
            placementPending: {
              ...s.placementPending,
              [territoryId]: (s.placementPending[territoryId] ?? 0) + 1,
            },
          }
    ),
  setPlacementDone: (placementDone) => set({ placementDone }),
  setReinforceBatch: (reinforceBatch) => set({ reinforceBatch }),
  setLegalActions: (legalActions) => set({ legalActions }),
  setFinishedObjective: (finishedObjective) => set({ finishedObjective }),
  setPacts: (pacts) => set({ pacts }),
  addPact: (pact) =>
    set((s) => ({ pacts: [...s.pacts.filter((p) => p.join('|') !== [...pact].sort().join('|')), [...pact].sort()] })),
  removePact: (pact) =>
    set((s) => ({ pacts: s.pacts.filter((p) => [...p].sort().join('|') !== [...pact].sort().join('|')) })),
  setPactProposalFrom: (pactProposalFrom) => set({ pactProposalFrom }),
  setConquestFlash: (territoryId) => set({ conquestFlash: { territoryId, ts: Date.now() } }),
  setTrophies: (trophies) => set({ trophies }),
  setRadialMenu: (radialMenu) => set({ radialMenu }),
  setTargetingMode: (targetingMode) => set({ targetingMode }),
  setFortifyPicker: (fortifyPicker) => set({ fortifyPicker }),
  startBattleRound: (round, ctx) =>
    set((s) => {
      const sameBattle =
        s.battle && s.battle.sourceId === ctx.sourceId && s.battle.targetId === ctx.targetId && !s.battle.conquered;
      if (sameBattle && s.battle) {
        return { battle: { ...s.battle, rounds: [...s.battle.rounds, round], open: true } };
      }
      return {
        battle: {
          sourceId: ctx.sourceId,
          targetId: ctx.targetId,
          attackerId: ctx.attackerId,
          defenderId: ctx.defenderId,
          attackerInitial: ctx.attackerBefore,
          defenderInitial: ctx.defenderBefore,
          rounds: [round],
          conquered: false,
          open: true,
        },
      };
    }),
  markBattleConquered: (territoryId) =>
    set((s) =>
      s.battle && s.battle.targetId === territoryId
        ? { battle: { ...s.battle, conquered: true } }
        : {},
    ),
  closeBattle: () => set((s) => (s.battle ? { battle: { ...s.battle, open: false } } : {})),
  hasPactWith: (playerId) => {
    const you = get().youId;
    if (!you || !playerId) return false;
    const key = [you, playerId].sort().join('|');
    return get().pacts.some((p) => [...p].sort().join('|') === key);
  },
  updateTerritory: (t) => set((s) => ({ territories: { ...s.territories, [t.id]: t } })),
  setSelectedSourceTerritory: (selectedSourceTerritory) => set({ selectedSourceTerritory }),
  setSelectedTargetTerritory: (selectedTargetTerritory) => set({ selectedTargetTerritory }),
  addChat: (entry) => set((s) => ({ chat: [...s.chat.slice(-99), entry] })),
  setDice: (lastDice) => set({ lastDice }),
  setAttack: (lastAttack) => set({ lastAttack }),
  pushReaction: (emoji, fromPlayerId) =>
    set((s) => ({ lastReaction: { id: (s.lastReaction?.id ?? 0) + 1, emoji, fromPlayerId } })),
  pushWagerResult: (playerId, won, wagered, payout) =>
    set((s) => ({ lastWager: { id: (s.lastWager?.id ?? 0) + 1, playerId, won, wagered, payout } })),
  addAiComment: (comment) => set((s) => ({ aiComments: [...s.aiComments.slice(-4), comment] })),
  setAiMuted: (aiMuted) => set({ aiMuted }),
  setSoundsMuted: (soundsMuted) => set({ soundsMuted }),
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
