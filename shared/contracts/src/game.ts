import { z } from 'zod';
import { PublicPlayer } from './player';
import { TerritoryState } from './map';

export const GameStatus = z.enum(['draft', 'lobby', 'ready', 'running', 'paused', 'finished', 'cancelled']);
export type GameStatus = z.infer<typeof GameStatus>;

/** Vista mínima de partida (join, snapshot). */
export const GameRef = z.object({
  id: z.string(),
  code: z.string(),
  name: z.string(),
  status: GameStatus,
  // qué mapa juega esta partida (classic_26 | classic_50 | mega_world_100)
  game_mode: z.string().optional(),
  map_assets: z
    .object({
      base_svg: z.string(),
      static_background_webp: z.string().nullable().optional(),
    })
    .nullable()
    .optional(),
});
export type GameRef = z.infer<typeof GameRef>;

/** Partida completa (endpoints admin). config es dict libre con estos campos sembrados. */
export const AdminGame = GameRef.extend({
  config: z.record(z.string(), z.unknown()),
  state: z.record(z.string(), z.unknown()),
  created_at: z.string(),
  updated_at: z.string(),
});
export type AdminGame = z.infer<typeof AdminGame>;

export const TurnPhase = z.enum(['reinforcement', 'attack', 'fortify']);
export type TurnPhase = z.infer<typeof TurnPhase>;

/** Estado de turno del motor: order = ids de jugadores, index apunta al actual. */
export const TurnState = z.object({
  order: z.array(z.string()),
  index: z.number().int(),
  turn_number: z.number().int(),
  phase: TurnPhase.default('attack'),
  reinforcements_available: z.number().int().default(0),
  wager: z.number().int().default(0),
});
export type TurnState = z.infer<typeof TurnState>;

export const CardSymbol = z.enum(['ship', 'cannon', 'balloon', 'joker']);
export type CardSymbol = z.infer<typeof CardSymbol>;

export const CountryCard = z.object({
  id: z.string(),
  territory_id: z.string(),
  symbol: CardSymbol,
});
export type CountryCard = z.infer<typeof CountryCard>;

export const SecretObjective = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string(),
});
export type SecretObjective = z.infer<typeof SecretObjective>;

export const GameStage = z.enum(['placement_1', 'placement_2', 'turns']);
export type GameStage = z.infer<typeof GameStage>;

/** Vista privada de la colocación inicial (solo lo tuyo + quiénes terminaron). */
export const PlacementView = z.object({
  remaining: z.number().int(),
  pending: z.record(z.string(), z.number().int()),
  players_done: z.array(z.string()),
});
export type PlacementView = z.infer<typeof PlacementView>;

/** payload de game.snapshot (efímero, al conectar el WS). */
export const SnapshotPayload = z.object({
  game: GameRef,
  you: z.string(),
  players: z.array(PublicPlayer),
  turn: TurnState.nullable(),
  // estado completo de territorios; sin este campo zod lo descartaría del
  // payload y el mapa quedaría sin datos (no interactivo)
  territories: z.record(z.string(), TerritoryState).optional(),
  // adyacencia del mapa activo (territorio -> vecinos): permite resaltar
  // objetivos atacables; zod descartaría el campo si no está declarado
  map_adjacency: z.record(z.string(), z.array(z.string())).optional(),
  recent_events: z.array(z.unknown()),
  stage: GameStage.optional(),
  placement: PlacementView.nullable().optional(),
  your_cards: z.array(CountryCard).optional(),
  your_objective: SecretObjective.nullable().optional(),
});
export type SnapshotPayload = z.infer<typeof SnapshotPayload>;
