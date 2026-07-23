import { useState } from 'react';
import { wsClient } from '../../services/websocket/wsClient';
import { audioService } from '../../services/audio/AudioService';

export interface FloatingEmoteItem {
  id: string;
  emoji: string;
  x: number;
  y: number;
}

const REACTION_EMOJIS = ['🍿', '💀', '🤡', '🔥', '💩', '💸'];

export function FloatingEmotes() {
  const [emotes, setEmotes] = useState<FloatingEmoteItem[]>([]);

  function triggerEmote(emoji: string) {
    audioService.unlock();
    // Enviar al chat como mensaje rápido
    wsClient.send({
      type: 'chat.send',
      payload: { text: emoji },
    });

    // Agregar animación local flotante
    const newItem: FloatingEmoteItem = {
      id: Math.random().toString(),
      emoji,
      x: 30 + Math.random() * 40, // Porcentaje X del mapa
      y: 40 + Math.random() * 30, // Porcentaje Y del mapa
    };

    setEmotes((prev) => [...prev.slice(-15), newItem]);

    setTimeout(() => {
      setEmotes((prev) => prev.filter((item) => item.id !== newItem.id));
    }, 2500);
  }

  return (
    <>
      {/* Botones de Reacción Rápida (Flotantes en la esquina del mapa) */}
      <div className="absolute top-3 right-3 z-20 flex gap-1.5 rounded-full border border-war-700 bg-war-950/80 p-1.5 backdrop-blur-md shadow-lg">
        {REACTION_EMOJIS.map((emoji) => (
          <button
            key={emoji}
            onClick={(e) => {
              e.stopPropagation();
              triggerEmote(emoji);
            }}
            className="flex h-8 w-8 items-center justify-center rounded-full text-base transition-transform hover:scale-125 hover:bg-war-800 active:scale-95"
            title={`Reaccionar con ${emoji}`}
          >
            {emoji}
          </button>
        ))}
      </div>

      {/* Renderizado de Emotes Flotantes sobre el mapa */}
      <div className="pointer-events-none absolute inset-0 z-30 overflow-hidden">
        {emotes.map((item) => (
          <div
            key={item.id}
            className="absolute text-4xl animate-bounce transition-all duration-1000"
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
