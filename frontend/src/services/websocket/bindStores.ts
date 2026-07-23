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
    const snap = p as z.infer<typeof SnapshotPayload>;
    game().applySnapshot(snap.game, snap.you, snap.players, snap.turn);
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
    const payload = p as z.infer<typeof GameStartedPayload>;
    for (const player of payload.players) game().upsertPlayer(player);
    game().setGameStatus('running');
    game().setTurn({ order: payload.turn_order, index: 0, turn_number: 1 });
    game().markStarted();
  });

  wsClient.on('turn.started', (p, env) => {
    const payload = p as z.infer<typeof TurnStartedPayload>;
    const turn = game().turn;
    if (turn && env.actor_id) {
      const index = turn.order.indexOf(env.actor_id);
      game().setTurn({ ...turn, index: index >= 0 ? index : turn.index, turn_number: payload.turn_number });
    }
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
  });

  wsClient.on('error', (p) => {
    const payload = p as z.infer<typeof ErrorPayload>;
    game().setError(payload.code, payload.message);
  });
}
