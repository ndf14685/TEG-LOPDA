import { useEffect, useState } from 'react';
import { useGameStore } from '../../state/gameStore';
import { assetRegistry } from '../../services/assets/AssetRegistry';
import { PLAYER_COLOR_VAR } from '../../utils/playerColors';

const EXPRESSION_GLYPH: Record<string, string> = {
  neutral: '🎙️', smug: '😏', shocked: '😱', laughing: '🤣', evil: '😈',
};

const TYPE_LABEL: Record<string, string> = {
  roast: 'BARDEO', praise: 'ELOGIO', narration: 'RELATO', drama: 'DRAMA', stats: 'DATOS',
};

const AUTO_MINIMIZE_MS = 12_000;

/** Panel del comentarista IA. No interrumpe: se minimiza solo. */
export function AICommentatorPanel() {
  const aiTyping = useGameStore((s) => s.aiTyping);
  const comments = useGameStore((s) => s.aiComments);
  const muted = useGameStore((s) => s.aiMuted);
  const setMuted = useGameStore((s) => s.setAiMuted);
  const playerById = useGameStore((s) => s.playerById);
  const [minimized, setMinimized] = useState(false);

  const latest = comments[comments.length - 1];

  useEffect(() => {
    if (!latest) return;
    setMinimized(false);
    const t = setTimeout(() => setMinimized(true), AUTO_MINIMIZE_MS);
    return () => clearTimeout(t);
  }, [latest]);

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
            {latest ? EXPRESSION_GLYPH[latest.expression] ?? '🎙️' : assetRegistry.emoji('avatar.comentarista.001', '🎙️')}
          </span>
          <h3 className="font-display text-sm font-bold tracking-wide text-gold-400">EL RELATOR</h3>
        </div>
        <button className="text-xs text-stone-400 hover:text-stone-200" onClick={() => setMuted(true)} aria-label="Silenciar comentarista">🔇</button>
      </header>

      {aiTyping && (
        <p data-testid="ai-typing" className="animate-pulse text-sm text-stone-400">escribiendo maldades…</p>
      )}

      {latest && !minimized && (
        <div data-testid="ai-comment" className="rounded-md bg-war-800 p-3">
          <div className="mb-1 flex items-center gap-2 text-[10px] tracking-wider">
            <span className="rounded bg-red-900/60 px-1.5 py-0.5 text-red-200">{TYPE_LABEL[latest.type] ?? latest.type}</span>
            {target && (
              <span style={{ color: PLAYER_COLOR_VAR[target.color] }}>→ {target.nickname}</span>
            )}
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
