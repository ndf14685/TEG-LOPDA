import { useEffect, useState } from 'react';
import { useGameStore } from '../../state/gameStore';

/** Toast no bloqueante con el resultado de la auto-apuesta al cerrar el turno. */
export function WagerToast() {
  const lastWager = useGameStore((s) => s.lastWager);
  const playerById = useGameStore((s) => s.playerById);
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (!lastWager) return;
    setShow(true);
    const t = setTimeout(() => setShow(false), 4500);
    return () => clearTimeout(t);
  }, [lastWager?.id]);

  if (!show || !lastWager) return null;
  const who = playerById(lastWager.playerId)?.nickname ?? 'Alguien';

  return (
    <div className="pointer-events-none fixed inset-x-0 top-4 z-50 flex justify-center px-4">
      <div
        data-testid="wager-toast"
        className={`pointer-events-auto rounded-xl border px-4 py-2 text-center text-sm font-bold shadow-2xl ${
          lastWager.won
            ? 'border-emerald-500/60 bg-emerald-950/90 text-emerald-200'
            : 'border-red-500/60 bg-red-950/90 text-red-200'
        }`}
      >
        {lastWager.won
          ? `🎉 ${who} ganó la apuesta: arriesgó ${lastWager.wagered} y cobra +${lastWager.payout} refuerzos el próximo turno`
          : `💸 ${who} perdió la apuesta: se fue con ${lastWager.wagered} refuerzos`}
      </div>
    </div>
  );
}
