import { useEffect, useState } from 'react';
import { useGameStore } from '../../state/gameStore';
import { colorValue } from '../../utils/playerColors';
import { audioService } from '../../services/audio/AudioService';

/** Emociones del backend (ai/commentator.py) → glifo. */
const EMOTION_GLYPH: Record<string, string> = {
  neutral: '🎙️', mocking: '😏', excited: '🤩', dramatic: '😱', deadpan: '😐',
};

const AUTO_MINIMIZE_MS = 12_000;

/** Panel del comentarista IA. No interrumpe: se minimiza solo. */
export function AICommentatorPanel() {
  const comments = useGameStore((s) => s.aiComments);
  const muted = useGameStore((s) => s.aiMuted);
  const setMutedStore = useGameStore((s) => s.setAiMuted);
  const playerById = useGameStore((s) => s.playerById);
  // activar/silenciar también sincroniza el canal de voz del relator
  const setMuted = (m: boolean) => {
    setMutedStore(m);
    audioService.unlock();
    audioService.setMuted('ai', m);
  };
  const [minimized, setMinimized] = useState(false);

  const latest = comments[comments.length - 1];

  useEffect(() => {
    if (!latest || muted) return;
    setMinimized(false);
    audioService.speakText(latest.text);
    const t = setTimeout(() => setMinimized(true), AUTO_MINIMIZE_MS);
    return () => clearTimeout(t);
  }, [latest, muted]);

  if (muted) {
    return (
      <div className="rounded-lg border border-war-700 bg-war-900 p-3 text-sm text-stone-500">
        🔇 Comentarista silenciado
        <button className="ml-2 underline hover:text-stone-300" onClick={() => setMuted(false)}>activar</button>
      </div>
    );
  }

  const target = latest ? playerById(latest.targetPlayerId) : undefined;

  return (
    <section aria-label="Comentarista IA" data-testid="ai-commentator" className="rounded-lg border border-war-700 bg-war-900 p-3">
      <header className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl" aria-hidden>
            {latest ? EMOTION_GLYPH[latest.emotion] ?? '🎙️' : '🎙️'}
          </span>
          <h3 className="font-display text-sm font-bold tracking-wide text-gold-400">EL RELATOR</h3>
        </div>
        <button className="text-xs text-stone-400 hover:text-stone-200" onClick={() => setMuted(true)} aria-label="Silenciar comentarista">🔇</button>
      </header>

      {!latest && <p className="text-sm italic text-stone-600">Afinando el micrófono…</p>}

      {latest && !minimized && (
        <div data-testid="ai-comment" className="rounded-md bg-war-800 p-3">
          <div className="mb-1 flex items-center gap-2 text-[10px] tracking-wider">
            <span className="rounded bg-red-900/60 px-1.5 py-0.5 text-red-200">{latest.emotion.toUpperCase()}</span>
            {target && <span style={{ color: colorValue(target.color) }}>→ {target.nickname}</span>}
          </div>
          <p className="text-sm leading-snug">{latest.text}</p>
        </div>
      )}

      {latest && minimized && (
        <button className="w-full truncate rounded bg-war-800/60 px-2 py-1 text-left text-xs text-stone-500 hover:text-stone-300" onClick={() => setMinimized(false)}>
          💬 {latest.text}
        </button>
      )}

      {comments.length > 1 && (
        <details className="mt-2 text-xs text-stone-500">
          <summary className="cursor-pointer">historial ({comments.length - 1})</summary>
          <ul className="mt-1 space-y-1">
            {comments.slice(0, -1).reverse().map((c) => (
              <li key={c.id} className="truncate">{c.text}</li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
