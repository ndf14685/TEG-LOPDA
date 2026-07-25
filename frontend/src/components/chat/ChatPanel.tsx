import { useEffect, useRef, useState, type FormEvent } from 'react';
import { useGameStore } from '../../state/gameStore';
import { useSessionStore } from '../../state/sessionStore';
import { wsClient } from '../../services/websocket/wsClient';
import { colorValue } from '../../utils/playerColors';

export function ChatPanel({ compact = false }: { compact?: boolean }) {
  const chat = useGameStore((s) => s.chat);
  const players = useGameStore((s) => s.players);
  const playerById = useGameStore((s) => s.playerById);
  const session = useSessionStore((s) => s.session);
  const [text, setText] = useState('');
  // '' = todos; un player_id = mensaje privado 🔒 a ese jugador
  const [target, setTarget] = useState('');
  const listRef = useRef<HTMLUListElement>(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [chat.length]);

  const recipients = players.filter(
    (p) => p.id !== session?.playerId && (p.role === 'player' || p.role === 'admin') && !p.eliminated,
  );

  function submit(e: FormEvent) {
    e.preventDefault();
    const trimmed = text.trim().slice(0, 500);
    if (!trimmed) return;
    wsClient.send({
      type: 'chat.send',
      payload: target ? { text: trimmed, target_player_id: target } : { text: trimmed },
    });
    setText('');
  }

  const targetPlayer = target ? playerById(target) : undefined;

  return (
    <div className={`flex flex-col ${compact ? 'h-36' : 'h-52'}`} data-testid="chat-panel">
      <ul ref={listRef} className="flex-1 space-y-1 overflow-y-auto rounded-t-lg border border-war-700 bg-war-900 p-2 text-sm" aria-live="polite" aria-label="Chat">
        {chat.map((msg) => {
          const author = playerById(msg.playerId);
          return (
            <li key={msg.id} className={`break-words ${msg.private ? 'rounded bg-purple-950/40 px-1' : ''}`}>
              {msg.private && <span className="mr-1 text-[10px] text-purple-300">🔒</span>}
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
        <select
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          aria-label="Destinatario"
          data-testid="chat-target"
          className={`w-24 shrink-0 rounded-bl-lg border border-t-0 border-war-700 px-1.5 py-1.5 text-xs outline-none ${
            target ? 'bg-purple-950/70 text-purple-200' : 'bg-war-800 text-stone-400'
          }`}
        >
          <option value="">Todos</option>
          {recipients.map((p) => (
            <option key={p.id} value={p.id}>privado: {p.nickname}</option>
          ))}
        </select>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={500}
          placeholder={targetPlayer ? `Privado a ${targetPlayer.nickname}…` : 'Escribí algo picante…'}
          aria-label="Mensaje de chat"
          className="min-w-0 flex-1 border border-l-0 border-t-0 border-war-700 bg-war-800 px-3 py-1.5 text-sm outline-none focus:border-gold-500"
        />
        <button type="submit" className="rounded-br-lg border border-l-0 border-t-0 border-war-700 bg-war-700 px-4 text-sm font-semibold hover:bg-war-800">
          Enviar
        </button>
      </form>
    </div>
  );
}
