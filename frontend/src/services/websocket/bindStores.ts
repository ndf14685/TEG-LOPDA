import { z } from 'zod';
import {
  LobbyStatePayload,
  ChatMessagePayload,
  GameStartingPayload,
  GameStartedPayload,
  SnapshotPayload,
  TauntTriggeredPayload,
  AICommentGeneratedPayload,
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
    if (status === 'reconnecting') conn().setSyncState('syncing');
  });

  wsClient.on('sync.lost', () => conn().setSyncState('syncing'));

  wsClient.on('lobby.state', (p) => game().applyLobby(p as z.infer<typeof LobbyStatePayload>));

  wsClient.on('chat.message', (p) => game().addChat(p as z.infer<typeof ChatMessagePayload>));

  wsClient.on('game.starting', (p) => game().setCountdown((p as z.infer<typeof GameStartingPayload>).countdownMs));

  wsClient.on('game.started', (p) => {
    game().applySnapshot((p as z.infer<typeof GameStartedPayload>).snapshot);
    game().setCountdown(null);
    conn().setSyncState('synced');
  });

  wsClient.on('game.snapshot', (p) => {
    game().applySnapshot((p as z.infer<typeof SnapshotPayload>).snapshot);
    conn().setSyncState('synced');
  });

  wsClient.on('taunt.triggered', (p) => {
    const taunt = p as z.infer<typeof TauntTriggeredPayload>;
    game().setTaunt({ ...taunt, receivedAt: Date.now() });
    audioService.playTauntBeep();
  });

  wsClient.on('ai.comment.typing', () => game().setAiTyping(true));
  wsClient.on('ai.comment.cancelled', () => game().setAiTyping(false));
  wsClient.on('ai.comment.error', () => game().setAiTyping(false));
  wsClient.on('ai.comment.generated', (p) => {
    game().addAiComment((p as z.infer<typeof AICommentGeneratedPayload>).comment);
  });
}
