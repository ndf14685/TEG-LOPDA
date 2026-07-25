import { useEffect, useRef, useState } from 'react';
import { useGameStore } from '../../state/gameStore';
import { useSessionStore } from '../../state/sessionStore';
import { colorValue } from '../../utils/playerColors';
import { audioService } from '../../services/audio/AudioService';

const PHASE_INSTRUCTION: Record<string, (n: number) => string> = {
  reinforcement: (n) => `Tenés ${n} tropas para colocar — tocá tus países`,
  attack: () => 'Tocá un país tuyo y elegí ⚔️ Atacar',
  fortify: () => 'Mové tropas ociosas hacia tus fronteras',
};

const PHASE_TITLE: Record<string, string> = {
  reinforcement: 'FASE: REFUERZOS',
  attack: 'FASE: ATAQUE',
  fortify: 'FASE: REAGRUPAMIENTO',
};

/** Banner central breve al empezar tu turno o cambiar de fase (nunca un
 * textito perdido en una esquina). Se desvanece solo. */
export function TurnBanner() {
  const turn = useGameStore((s) => s.turn);
  const stage = useGameStore((s) => s.stage);
  const currentPlayerId = useGameStore((s) => s.currentPlayerId);
  const playerById = useGameStore((s) => s.playerById);
  const session = useSessionStore((s) => s.session);
  const [banner, setBanner] = useState<{ key: string; title: string; phase: string; sub: string; color: string } | null>(null);
  const lastKey = useRef('');

  const currentId = currentPlayerId();
  const phase = turn?.phase ?? '';
  const reinf = turn?.reinforcements_available ?? 0;

  useEffect(() => {
    if (!turn || stage !== 'turns' || !currentId) return;
    const key = `${turn.turn_number}:${currentId}:${phase}`;
    if (key === lastKey.current) return;
    const turnChanged = !lastKey.current.startsWith(`${turn.turn_number}:${currentId}`);
    lastKey.current = key;

    const me = currentId === session?.playerId;
    const player = playerById(currentId);
    if (!player) return;

    if (me) {
      setBanner({
        key,
        title: turnChanged ? `${player.nickname.toUpperCase()}, JUGÁS VOS` : PHASE_TITLE[phase] ?? phase,
        phase: turnChanged ? PHASE_TITLE[phase] ?? phase : '',
        sub: PHASE_INSTRUCTION[phase]?.(reinf) ?? '',
        color: colorValue(player.color),
      });
      if (turnChanged) audioService.playGameSound('audio.ui.notify', [880, 1175]);
    } else if (turnChanged) {
      setBanner({
        key,
        title: `ESTÁ JUGANDO ${player.nickname.toUpperCase()}`,
        phase: PHASE_TITLE[phase] ?? phase,
        sub: 'Mirá La Tribuna mientras esperás',
        color: colorValue(player.color),
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [turn?.turn_number, currentId, phase, stage]);

  useEffect(() => {
    if (!banner) return;
    const t = window.setTimeout(() => setBanner(null), 3000);
    return () => window.clearTimeout(t);
  }, [banner]);

  if (!banner) return null;
  return (
    <div key={banner.key} className="turn-banner-overlay" data-testid="turn-banner" aria-live="polite">
      <div
        className="rounded-2xl border-2 bg-war-950/95 px-10 py-5 shadow-2xl backdrop-blur-md"
        style={{ borderColor: banner.color, boxShadow: `0 0 40px ${banner.color}66` }}
      >
        <p className="font-display text-3xl font-black tracking-wide" style={{ color: banner.color }}>
          {banner.title}
        </p>
        {banner.phase && <p className="mt-1 text-sm font-bold text-gold-400">{banner.phase}</p>}
        {banner.sub && <p className="mt-1 text-sm text-stone-300">{banner.sub}</p>}
      </div>
    </div>
  );
}
