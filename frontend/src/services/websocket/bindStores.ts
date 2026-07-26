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
  StatsReadyPayload,
  WagerPlacedPayload,
  WagerResolvedPayload,
} from '@teg/contracts';
import { wsClient } from './wsClient';
import { REACTION_SET } from '../../config/reactions';
import { useGameStore } from '../../state/gameStore';
import { useConnectionStore } from '../../state/connectionStore';
import { audioService } from '../audio/AudioService';
import { playtestClient } from '../playtest/playtestClient';

let bound = false;

/** Conecta el stream WS validado con los stores. Idempotente. */
export function bindWsToStores(): void {
  if (bound) return;
  bound = true;

  const game = () => useGameStore.getState();
  const conn = () => useConnectionStore.getState();

  wsClient.onStatus((status) => {
    conn().setWsStatus(status);
    playtestClient.track(`websocket.${status}`, {});
    if (status === 'reconnecting' || status === 'connecting') conn().setSyncState('syncing');
  });

  wsClient.on('sync.lost', () => {
    conn().setSyncState('syncing');
    playtestClient.track('sync.lost', {});
  });

  wsClient.on('*', (_p, env) => {
    playtestClient.track(env.event_type, { actor_id: env.actor_id, target_id: env.target_id }, {
      event_id: env.event_id,
      sequence_number: env.sequence_number,
    });
  });

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
    const snapExtra = p as { pacts?: string[][]; pact_proposal_from?: string | null };
    game().setPacts(snapExtra.pacts ?? []);
    game().setPactProposalFrom(snapExtra.pact_proposal_from ?? null);
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
    // el turno se setea siempre: el orden ya está sorteado y turn.started
    // necesita la lista para mapear el índice (la UI lo oculta en colocación)
    {
      game().setTurn({
        order: payload.turn_order,
        index: 0,
        turn_number: 1,
        phase: payload.phase ?? 'reinforcement',
        reinforcements_available: payload.reinforcements_available ?? 3,
        wager: 0,
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
    // el turno nuevo cierra la arena y cualquier puntería pendiente
    game().closeBattle();
    game().setTargetingMode(null);
    game().setRadialMenu(null);
    game().setFortifyPicker(null);
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

  wsClient.on('wager.placed', (p) => {
    const payload = p as z.infer<typeof WagerPlacedPayload>;
    game().setTurn(payload.turn);
  });

  wsClient.on('wager.resolved', (p, env) => {
    const payload = p as z.infer<typeof WagerResolvedPayload>;
    game().pushWagerResult(env.actor_id ?? payload.player_id, payload.won, payload.wagered, payload.payout);
    game().pushReaction(payload.won ? '🎉' : '💸', env.actor_id ?? payload.player_id);
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
    const payload = p as z.infer<typeof AttackResolvedPayload> & {
      source_territory_id?: string | null;
      target_territory_id?: string | null;
      attacker_armies_before?: number | null;
      defender_armies_before?: number | null;
      attacker_armies_after?: number | null;
      defender_armies_after?: number | null;
    };
    game().setAttack({
      attackerId: env.actor_id ?? null,
      defenderId: env.target_id ?? null,
      attackerDice: payload.attacker_dice,
      defenderDice: payload.defender_dice,
      attackerLosses: payload.attacker_losses,
      defenderLosses: payload.defender_losses,
      ts: env.timestamp,
    });
    // la Arena acumula rondas de la MISMA batalla (origen→destino)
    if (payload.source_territory_id && payload.target_territory_id) {
      game().startBattleRound(
        {
          attackerDice: payload.attacker_dice,
          defenderDice: payload.defender_dice,
          attackerLosses: payload.attacker_losses,
          defenderLosses: payload.defender_losses,
          comparisons: payload.comparisons,
          attackerAfter: payload.attacker_armies_after ?? null,
          defenderAfter: payload.defender_armies_after ?? null,
        },
        {
          sourceId: payload.source_territory_id,
          targetId: payload.target_territory_id,
          attackerId: env.actor_id ?? null,
          defenderId: env.target_id ?? null,
          attackerBefore: payload.attacker_armies_before ?? 0,
          defenderBefore: payload.defender_armies_before ?? 0,
        },
      );
    }
    audioService.playGameSound('audio.gameplay.battle_clash', [140, 90]);
  });

  wsClient.on('territory.conquered', (p, env) => {
    const payload = p as { territory?: { id?: string } };
    if (payload.territory?.id) {
      game().setConquestFlash(payload.territory.id);
      game().markBattleConquered(payload.territory.id);
    }
    game().pushReaction('🔥', env.actor_id ?? null); // momento compartido para todos
    const you = game().youId;
    if (env.target_id === you) {
      audioService.playGameSound('audio.gameplay.territory_lost', [330, 220]);
    } else {
      audioService.playGameSound('audio.gameplay.conquest_success', [262, 330, 392, 523]);
    }
  });

  wsClient.on('player.eliminated', (_p, env) => {
    game().pushReaction('💀', env.target_id ?? null); // se lo ve toda la mesa
    const you = game().youId;
    audioService.playGameSound(
      env.target_id === you ? 'audio.gameplay.defeat_sad' : 'audio.gameplay.player_eliminated',
      [392, 311, 233],
    );
  });

  wsClient.on('pact.proposed', (_p, env) => {
    if (env.target_id === game().youId) {
      game().setPactProposalFrom(env.actor_id ?? null);
      audioService.playGameSound('audio.ui.notify', [880, 1175]);
    }
  });

  wsClient.on('pact.accepted', (_p, env) => {
    const a = env.actor_id, b = env.target_id;
    if (a && b) game().addPact([a, b]);
    if (b === game().youId) game().setPactProposalFrom(null);
    audioService.playGameSound('audio.ui.notify', [880, 1175]);
  });

  wsClient.on('pact.rejected', (_p, env) => {
    if (env.target_id === game().youId) game().setPactProposalFrom(null);
  });

  wsClient.on('pact.broken', (_p, env) => {
    const a = env.actor_id, b = env.target_id;
    if (a && b) game().removePact([a, b]);
    audioService.playGameSound('audio.gameplay.traitor_alert', [466, 494, 155]);
  });

  wsClient.on('chat.message', (p, env) => {
    const text = (p as z.infer<typeof ChatMessagePayload>).text;
    // Una reacción (emoji suelto) flota en la pantalla de TODOS y no ensucia
    // el chat: es efímera y compartida, para los que esperan turno también.
    if (REACTION_SET.has(text.trim())) {
      game().pushReaction(text.trim(), env.actor_id ?? null);
      return;
    }
    game().addChat({
      id: env.event_id,
      playerId: env.actor_id ?? null,
      text,
      private: env.visibility === 'private',
      ts: env.timestamp,
    });
  });

  wsClient.on('taunt.triggered', (p, env) => {
    const payload = p as z.infer<typeof TauntTriggeredPayload> & { audio_url?: string };
    game().setTaunt({
      fromPlayerId: env.actor_id ?? null,
      toPlayerId: env.target_id ?? null,
      audioAssetId: payload.audio_asset_id,
      sourceEventType: payload.source_event_type,
      receivedAt: Date.now(),
    });
    if (payload.audio_url) {
      // audio grabado por el jugador: se sirve directo del backend
      audioService.playTauntUrl(payload.audio_url);
    } else {
      audioService.playTauntAsset(payload.audio_asset_id);
    }
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
    audioService.playGameSound(
      payload.winner_player_id === game().youId
        ? 'audio.gameplay.victory_fanfare'
        : 'audio.gameplay.player_eliminated',
      [392, 523, 659, 784],
    );
  });

  wsClient.on('stats.ready', (p) => {
    const payload = p as z.infer<typeof StatsReadyPayload>;
    game().setTrophies(payload.trophies);
  });

  wsClient.on('error', (p) => {
    const payload = p as z.infer<typeof ErrorPayload>;
    game().setError(payload.code, payload.message);
    playtestClient.reportTechnical({
      category: 'action-did-not-work',
      title: `Backend rechazó acción: ${payload.code}`,
      message: payload.message,
      error_type: 'backend-error-event',
      component: 'wsClient',
      code: payload.code,
      phase: game().turn?.phase ?? undefined,
    });
  });
}
