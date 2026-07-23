import { useEffect, useMemo, useState } from 'react';
import { FALLBACK_SOUNDBOARD, SOUNDBOARD_COOLDOWN_MS } from '../../config/soundboard.config';
import { wsClient } from '../../services/websocket/wsClient';
import { Cooldown } from '../../services/audio/TauntQueue';
import { audioService } from '../../services/audio/AudioService';
import { assetRegistry } from '../../services/assets/AssetRegistry';
import { useGameStore } from '../../state/gameStore';
import { colorValue } from '../../utils/playerColors';

const cooldown = new Cooldown(SOUNDBOARD_COOLDOWN_MS);
const TAUNT_TOAST_MS = 5000;

/**
 * Bardeo rápido. Los botones salen del taunts-manifest de Dirección de Arte
 * (fallback local si falta). Viajan como chat: el backend aún no tiene un
 * mensaje cliente de taunt (los taunt.triggered los dispara el server por
 * eventos de juego configurados por el admin).
 */
export function SoundboardBar() {
  const lastTaunt = useGameStore((s) => s.lastTaunt);
  const setTaunt = useGameStore((s) => s.setTaunt);
  const playerById = useGameStore((s) => s.playerById);
  const [blocked, setBlocked] = useState(false);

  const buttons = useMemo(() => assetRegistry.soundboardButtons(FALLBACK_SOUNDBOARD), []);

  useEffect(() => {
    if (!lastTaunt) return;
    const t = setTimeout(() => setTaunt(null), TAUNT_TOAST_MS);
    return () => clearTimeout(t);
  }, [lastTaunt, setTaunt]);

  function fire(id: string) {
    const btn = buttons.find((b) => b.id === id);
    if (!btn) return;
    if (!cooldown.tryUse()) {
      setBlocked(true);
      setTimeout(() => setBlocked(false), 1200);
      return;
    }
    wsClient.send({ type: 'chat.send', payload: { text: `📢 ${btn.label.toUpperCase()}` } });
    audioService.playSoundboardSound(btn.soundPath);
  }

  const from = lastTaunt ? playerById(lastTaunt.fromPlayerId) : undefined;
  const to = lastTaunt ? playerById(lastTaunt.toPlayerId) : undefined;

  return (
    <div data-testid="soundboard">
      <div className="flex flex-wrap gap-1.5">
        {buttons.map((btn) => (
          <button
            key={btn.id}
            onClick={() => fire(btn.id)}
            className="rounded-full border border-war-700 bg-war-800 px-3 py-1 text-xs hover:border-gold-500 hover:text-gold-400 active:scale-95 transition-transform"
          >
            {btn.label}
          </button>
        ))}
      </div>
      {blocked && <p className="mt-1 text-xs text-yellow-500">⏳ Pará un poco con el spam…</p>}
      {lastTaunt && (
        <div data-testid="taunt-toast" role="status" className="mt-2 flex items-center gap-2 rounded-lg border border-gold-500/40 bg-war-800 px-3 py-1.5 text-sm">
          <span aria-hidden>📣</span>
          <span className="font-semibold" style={{ color: colorValue(from?.color) }}>{from?.nickname ?? '???'}</span>
          <span className="text-stone-300">le manda un audio a</span>
          <span className="font-semibold" style={{ color: colorValue(to?.color) }}>{to?.nickname ?? 'la sala'}</span>
          <span className="text-xs text-stone-500">({lastTaunt.sourceEventType})</span>
        </div>
      )}
    </div>
  );
}
