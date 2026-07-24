import { z } from 'zod';
import {
  SnapshotPayload,
  PlayerJoinedPayload,
  PlayerReadyPayload,
  PresenceChangedPayload,
  GameStartedPayload,
  TurnStartedPayload,
  DiceRolledPayload,
  AttackResolvedPayload,
  ChatMessagePayload,
  TauntTriggeredPayload,
  AICommentGeneratedPayload,
  GameFinishedPayload,
  ErrorPayload,
  GameEventEnvelope,
  PlacementStartedPayload,
  PlacementUpdatedPayload,
  PlacementProgressPayload,
  PlacementRevealedPayload,
  CardsHandPayload,
  CardsTradedPayload,
  ObjectiveAssignedPayload,
  LegalActionsPayload,
} from '@teg/contracts';
import { wsClient } from './wsClient';
import { useGameStore } from '../../state/gameStore';
import { useConnectionStore } from '../../state/connectionStore';
import { audioService } from '../audio/AudioService';

let bound = false;

/** Conecta el stream WS validado con los stores. Idempotente. */
export function bindWsToStores(): void {
  if (bound) return;
  bound = true;

  const game = () => useGameStore.getState();
  const conn = () => useConnectionStore.getState();

  wsClient.onStatus((status) => {
    conn().setWsStatus(status);
    if (status === 'reconnecting' || status === 'connecting') conn().setSyncState('syncing');
  });

  wsClient.on('sync.lost', () => conn().setSyncState('syncing'));

  wsClient.on('game.snapshot', (p) => {
    const snap = p as z.infer<typeof SnapshotPayload> & { territories?: Record<string, any> };
    game().applySnapshot(snap.game, snap.you, snap.players, snap.turn, snap.territories, snap.map_adjacency);
    if (snap.territories) game().setTerritories(snap.territories);
    game().setStage(snap.stage ?? (snap.turn ? 'turns' : null));
    if (snap.placement) {
      game().setPlacement(snap.placement.remaining, snap.placement.pending);
    }
    game().setPlacementDone(snap.placement?.players_done ?? []);
    game().setCards(snap.your_cards ?? []);
    game().setSecretObjective(snap.your_objective ?? null);
    // el historial reciente rehidrata chat y comentarios tras una reconexión
    for (const raw of snap.recent_events) {
      const ev = GameEventEnvelope.safeParse(raw);
      if (!ev.success) continue;
      if (ev.data.event_type === 'chat.message') {
        const payload = ChatMessagePayload.safeParse(ev.data.payload);
        if (payload.success) {
          game().addChat({
            id: ev.data.event_id,
            playerId: ev.data.actor_id ?? null,
            text: payload.data.text,
            private: ev.data.visibility === 'private',
            ts: ev.data.timestamp,
          });
        }
      } else if (ev.data.event_type === 'ai.comment.generated') {
        const payload = AICommentGeneratedPayload.safeParse(ev.data.payload);
        if (payload.success) {
          game().addAiComment({
            id: ev.data.event_id,
            text: payload.data.text,
            emotion: payload.data.emotion,
            audioAsset: payload.data.audio_asset,
            targetPlayerId: ev.data.target_id ?? null,
            ts: ev.data.timestamp,
          });
        }
      }
    }
    conn().setSyncState('synced');
  });

  wsClient.on('player.joined', (p) => game().upsertPlayer((p as z.infer<typeof PlayerJoinedPayload>).player));

  wsClient.on('player.ready', (p, env) => {
    const payload = p as z.infer<typeof PlayerReadyPayload>;
    if (env.actor_id) game().patchPlayer(env.actor_id, { is_ready: payload.ready });
    game().setGameStatus(payload.game_status);
  });

  wsClient.on('presence.changed', (p, env) => {
    if (env.actor_id) game().patchPlayer(env.actor_id, { presence: (p as z.infer<typeof PresenceChangedPayload>).presence });
  });

  wsClient.on('player.kicked', (_p, env) => {
    if (env.actor_id) game().patchPlayer(env.actor_id, { presence: 'offline' });
  });

  wsClient.on('game.started', (p) => {
    const payload = p as z.infer<typeof GameStartedPayload> & {
      territories?: Record<string, any>;
      phase?: 'reinforcement' | 'attack' | 'fortify';
      reinforcements_available?: number;
    };
    for (const player of payload.players) game().upsertPlayer(player);
    if (payload.territories) game().setTerritories(payload.territories);
    game().setGameStatus('running');
    const stage = payload.stage as 'placement_1' | 'placement_2' | 'turns' | undefined;
    game().setStage(stage ?? 'turns');
    if (!stage || stage === 'turns') {
      game().setTurn({
        order: payload.turn_order,
        index: 0,
        turn_number: 1,
        phase: payload.phase ?? 'reinforcement',
        reinforcements_available: payload.reinforcements_available ?? 3,
      });
    }
    game().markStarted();
  });

  wsClient.on('placement.started', (p) => {
    const payload = p as z.infer<typeof PlacementStartedPayload>;
    game().setStage(payload.stage as 'placement_1' | 'placement_2');
    game().setPlacement(payload.pool_size, {});
    game().setPlacementDone([]);
  });

  wsClient.on('placement.updated', (p) => {
    const payload = p as z.infer<typeof PlacementUpdatedPayload>;
    game().setPlacement(payload.remaining, payload.pending);
  });

  wsClient.on('placement.progress', (p) => {
    const payload = p as z.infer<typeof PlacementProgressPayload>;
    if (payload.done && !game().placementDone.includes(payload.player_id)) {
      game().setPlacementDone([...game().placementDone, payload.player_id]);
    }
  });

  wsClient.on('placement.revealed', (p) => {
    const payload = p as z.infer<typeof PlacementRevealedPayload>;
    game().setTerritories(payload.territories as Record<string, { id: string; owner_player_id: string | null; armies: number }>);
    game().setStage(payload.next_stage as 'placement_1' | 'placement_2' | 'turns');
    game().setPlacementDone([]);
    if (payload.next_stage !== 'turns') game().setPlacement(3, {});
  });

  wsClient.on('cards.hand', (p) => {
    game().setCards((p as z.infer<typeof CardsHandPayload>).your_cards);
  });

  wsClient.on('cards.traded', (p) => {
    const payload = p as z.infer<typeof CardsTradedPayload>;
    if (payload.turn) game().setTurn(payload.turn);
  });

  wsClient.on('objective.assigned', (p) => {
    game().setSecretObjective((p as z.infer<typeof ObjectiveAssignedPayload>).objective);
  });

  wsClient.on('legal.actions', (p) => {
    game().setLegalActions((p as z.infer<typeof LegalActionsPayload>).actions as { action: string; params: Record<string, unknown> }[]);
  });

  wsClient.on('turn.started', (p, env) => {
    const payload = p as z.infer<typeof TurnStartedPayload> & {
      phase?: 'reinforcement' | 'attack' | 'fortify';
      reinforcements_available?: number;
    };
    const turn = game().turn;
    if (turn && env.actor_id) {
      const index = turn.order.indexOf(env.actor_id);
      game().setTurn({
        ...turn,
        index: index >= 0 ? index : turn.index,
        turn_number: payload.turn_number,
        phase: payload.phase ?? 'reinforcement',
        reinforcements_available: payload.reinforcements_available ?? turn.reinforcements_available,
      });
    }
  });

  wsClient.on('territory.updated', (p) => {
    const payload = p as { territory?: any; target_territory?: any; turn?: any };
    if (payload.territory) game().updateTerritory(payload.territory);
    if (payload.target_territory) game().updateTerritory(payload.target_territory);
    if (payload.turn) game().setTurn(payload.turn);
  });

  wsClient.on('dice.rolled', (p, env) => {
    const payload = p as z.infer<typeof DiceRolledPayload>;
    game().setDice({ playerId: env.actor_id ?? null, dice: payload.dice, ts: env.timestamp });
    audioService.playDiceSound();
  });

  wsClient.on('attack.resolved', (p, env) => {
    const payload = p as z.infer<typeof AttackResolvedPayload>;
    game().setAttack({
      attackerId: env.actor_id ?? null,
      defenderId: env.target_id ?? null,
      attackerDice: payload.attacker_dice,
      defenderDice: payload.defender_dice,
      attackerLosses: payload.attacker_losses,
      defenderLosses: payload.defender_losses,
      ts: env.timestamp,
    });
  });

  wsClient.on('chat.message', (p, env) => {
    game().addChat({
      id: env.event_id,
      playerId: env.actor_id ?? null,
      text: (p as z.infer<typeof ChatMessagePayload>).text,
      private: env.visibility === 'private',
      ts: env.timestamp,
    });
  });

  wsClient.on('taunt.triggered', (p, env) => {
    const payload = p as z.infer<typeof TauntTriggeredPayload>;
    game().setTaunt({
      fromPlayerId: env.actor_id ?? null,
      toPlayerId: env.target_id ?? null,
      audioAssetId: payload.audio_asset_id,
      sourceEventType: payload.source_event_type,
      receivedAt: Date.now(),
    });
    audioService.playTauntAsset(payload.audio_asset_id);
  });

  wsClient.on('ai.comment.generated', (p, env) => {
    const payload = p as z.infer<typeof AICommentGeneratedPayload>;
    game().addAiComment({
      id: env.event_id,
      text: payload.text,
      emotion: payload.emotion,
      audioAsset: payload.audio_asset,
      targetPlayerId: env.target_id ?? null,
      ts: env.timestamp,
    });
  });

  wsClient.on('game.paused', () => game().setGameStatus('paused'));
  wsClient.on('game.resumed', () => game().setGameStatus('running'));

  wsClient.on('game.finished', (p) => {
    const payload = p as z.infer<typeof GameFinishedPayload>;
    game().setGameStatus('finished');
    game().setFinished(payload.winner_player_id, payload.turns_played);
    game().setFinishedObjective(payload.objective ?? null);
  });

  wsClient.on('error', (p) => {
    const payload = p as z.infer<typeof ErrorPayload>;
    game().setError(payload.code, payload.message);
  });
}
