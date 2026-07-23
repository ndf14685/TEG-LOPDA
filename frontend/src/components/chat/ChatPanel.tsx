import { useEffect, useRef, useState, type FormEvent } from 'react';
import { useGameStore } from '../../state/gameStore';
import { wsClient } from '../../services/websocket/wsClient';
import { colorValue } from '../../utils/playerColors';

export function ChatPanel({ compact = false }: { compact?: boolean }) {
  const chat = useGameStore((s) => s.chat);
  const playerById = useGameStore((s) => s.playerById);
  const [text, setText] = useState('');
  const listRef = useRef<HTMLUListElement>(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [chat.length]);

  function submit(e: FormEvent) {
    e.preventDefault();
    const trimmed = text.trim().slice(0, 500);
    if (!trimmed) return;
    wsClient.send({ type: 'chat.send', payload: { text: trimmed } });
    setText('');
  }

  return (
    <div className={`flex flex-col ${compact ? 'h-32' : 'h-48'}`} data-testid="chat-panel">
      <ul ref={listRef} className="flex-1 space-y-1 overflow-y-auto rounded-t-lg border border-war-700 bg-war-900 p-2 text-sm" aria-live="polite" aria-label="Chat">
        {chat.map((msg) => {
          const author = playerById(msg.playerId);
          return (
            <li key={msg.id} className="break-words">
              {msg.private && <span className="mr-1 text-[10px] text-stone-500">🔒</span>}
              <span className="font-semibold" style={{ color: colorValue(author?.color) }}>
                {author?.nickname ?? '???'}:
              </span>{' '}
              {/* React escapa el contenido: nunca HTML crudo del usuario */}
              <span className="text-stone-300">{msg.text}</span>
            </li>
          );
        })}
        {chat.length === 0 && <li className="text-stone-600 italic">Silencio incómodo…</li>}
      </ul>
      <form onSubmit={submit} className="flex">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={500}
          placeholder="Escribí algo picante…"
          aria-label="Mensaje de chat"
          className="min-w-0 flex-1 rounded-bl-lg border border-t-0 border-war-700 bg-war-800 px-3 py-1.5 text-sm outline-none focus:border-gold-500"
        />
        <button type="submit" className="rounded-br-lg border border-l-0 border-t-0 border-war-700 bg-war-700 px-4 text-sm font-semibold hover:bg-war-800">
          Enviar
        </button>
      </form>
    </div>
  );
}
