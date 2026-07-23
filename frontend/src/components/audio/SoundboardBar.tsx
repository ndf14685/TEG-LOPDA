import { useEffect, useState } from 'react';
import { SOUNDBOARD_CONFIG, soundboardLabel } from '../../config/soundboard.config';
import { wsClient } from '../../services/websocket/wsClient';
import { Cooldown } from '../../services/audio/TauntQueue';
import { useGameStore } from '../../state/gameStore';
import { PLAYER_COLOR_VAR } from '../../utils/playerColors';

const cooldown = new Cooldown(SOUNDBOARD_CONFIG.cooldownMs);
const TAUNT_TOAST_MS = 4000;

export function SoundboardBar() {
  const lastTaunt = useGameStore((s) => s.lastTaunt);
  const setTaunt = useGameStore((s) => s.setTaunt);
  const playerById = useGameStore((s) => s.playerById);
  const [blocked, setBlocked] = useState(false);

  useEffect(() => {
    if (!lastTaunt) return;
    const t = setTimeout(() => setTaunt(null), TAUNT_TOAST_MS);
    return () => clearTimeout(t);
  }, [lastTaunt, setTaunt]);

  function fire(soundboardId: string) {
    if (!cooldown.tryUse()) {
      setBlocked(true);
      setTimeout(() => setBlocked(false), 1200);
      return;
    }
    wsClient.send({ type: 'taunt.trigger', soundboardId });
  }

  const from = lastTaunt ? playerById(lastTaunt.fromPlayerId) : undefined;

  return (
    <div data-testid="soundboard">
      <div className="flex flex-wrap gap-1.5">
        {SOUNDBOARD_CONFIG.buttons.map((btn) => (
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
          <span className="font-semibold" style={{ color: from ? PLAYER_COLOR_VAR[from.color] : undefined }}>{from?.nickname ?? '???'}</span>
          <span className="text-stone-300">manda:</span>
          <strong className="text-gold-400">«{soundboardLabel(lastTaunt.soundboardId)}»</strong>
          <button className="ml-auto text-xs" onClick={() => fire('soundboard.llora')} title="Responder con Llorá">😭 devolver</button>
        </div>
      )}
    </div>
  );
}
