import { useEffect, useRef, useState } from 'react';
import { wsClient } from '../../services/websocket/wsClient';
import { audioService } from '../../services/audio/AudioService';
import { useGameStore } from '../../state/gameStore';
import { REACTION_EMOJIS } from '../../config/reactions';

export interface FloatingEmoteItem {
  id: string;
  emoji: string;
  x: number;
  y: number;
}

export function FloatingEmotes() {
  const [emotes, setEmotes] = useState<FloatingEmoteItem[]>([]);
  const lastReaction = useGameStore((s) => s.lastReaction);
  const seenReactionId = useRef(0);

  function spawn(emoji: string) {
    const item: FloatingEmoteItem = {
      id: `${emoji}-${Math.random().toString(36).slice(2)}`,
      emoji,
      x: 20 + Math.random() * 55, // % sobre el mapa
      y: 35 + Math.random() * 40,
    };
    setEmotes((prev) => [...prev.slice(-20), item]);
    setTimeout(() => setEmotes((prev) => prev.filter((e) => e.id !== item.id)), 2500);
  }

  // Reacciones compartidas: cualquier jugador (o un evento como conquista)
  // hace flotar el emoji en la pantalla de TODOS. El emisor también lo ve por
  // el eco, así que la fuente única es el store: nada se anima solo localmente.
  useEffect(() => {
    if (!lastReaction || lastReaction.id === seenReactionId.current) return;
    seenReactionId.current = lastReaction.id;
    spawn(lastReaction.emoji);
  }, [lastReaction]);

  function react(emoji: string) {
    audioService.unlock();
    // Se difunde por el broadcast de chat; vuelve como reacción para todos.
    wsClient.send({ type: 'chat.send', payload: { text: emoji } });
  }

  return (
    <>
      <div className="absolute top-3 right-3 z-20 flex gap-1.5 rounded-full border border-war-700 bg-war-950/80 p-1.5 backdrop-blur-md shadow-lg">
        {REACTION_EMOJIS.map((emoji) => (
          <button
            key={emoji}
            data-testid={`reaction-${emoji}`}
            onClick={(e) => {
              e.stopPropagation();
              react(emoji);
            }}
            className="flex h-8 w-8 items-center justify-center rounded-full text-base transition-transform hover:scale-125 hover:bg-war-800 active:scale-95"
            title={`Reaccionar con ${emoji}`}
          >
            {emoji}
          </button>
        ))}
      </div>

      <div className="pointer-events-none absolute inset-0 z-30 overflow-hidden">
        {emotes.map((item) => (
          <div
            key={item.id}
            className="absolute text-4xl"
            style={{
              left: `${item.x}%`,
              top: `${item.y}%`,
              animation: 'floatUp 2.5s ease-out forwards',
            }}
          >
            {item.emoji}
          </div>
        ))}
      </div>
    </>
  );
}
