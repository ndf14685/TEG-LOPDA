import { useEffect, useState } from 'react';
import { useGameStore } from '../../state/gameStore';
import { PlayerAvatar } from '../players/PlayerAvatar';
import { Dice3D } from './Dice3D';
import { colorValue } from '../../utils/playerColors';

export function CombatOverlay() {
  const lastAttack = useGameStore((s) => s.lastAttack);
  const playerById = useGameStore((s) => s.playerById);
  const [visible, setVisible] = useState(false);
  const [isRolling, setIsRolling] = useState(true);

  useEffect(() => {
    if (!lastAttack) return;
    setVisible(true);
    setIsRolling(true);

    const rollTimer = setTimeout(() => setIsRolling(false), 600);
    const hideTimer = setTimeout(() => setVisible(false), 4500);

    return () => {
      clearTimeout(rollTimer);
      clearTimeout(hideTimer);
    };
  }, [lastAttack]);

  if (!visible || !lastAttack) return null;

  const attacker = playerById(lastAttack.attackerId);
  const defender = playerById(lastAttack.defenderId);

  const sortedAttacker = [...lastAttack.attackerDice].sort((a, b) => b - a);
  const sortedDefender = [...lastAttack.defenderDice].sort((a, b) => b - a);

  const pairsCount = Math.min(sortedAttacker.length, sortedDefender.length);

  return (
    // Panel no bloqueante: fijo abajo-centro, no cubre el tablero ni intercepta
    // clicks (wrapper pointer-events-none). Solo la tarjeta es interactiva y un
    // toque la cierra; además se autooculta. Lo ven todos sin frenar su juego.
    <div className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex justify-center px-4">
      <div
        className="pointer-events-auto relative w-full max-w-md cursor-pointer rounded-2xl border border-gold-500/40 bg-gradient-to-b from-war-900 via-war-950 to-stone-950 p-5 text-slate-100 shadow-2xl transition-opacity duration-300"
        onClick={() => setVisible(false)}
        title="Tocá para cerrar"
      >
        <button
          onClick={() => setVisible(false)}
          className="absolute right-4 top-4 text-stone-400 hover:text-stone-100"
          aria-label="Cerrar batalla"
        >
          ✕
        </button>

        {/* Encabezado del Combate */}
        <div className="mb-4 text-center">
          <span className="inline-block rounded-full bg-red-950/80 px-3 py-1 text-xs font-bold tracking-widest text-red-300 border border-red-800/60">
            ⚔️ BATALLA TÁCTICA
          </span>
          <h2 className="mt-2 font-display text-2xl font-black tracking-wide text-gold-400">
            {attacker?.nickname ?? 'Atacante'} <span className="text-stone-500">VS</span> {defender?.nickname ?? 'Defensor'}
          </h2>
        </div>

        {/* Duelistas: Avatares y Dados 3D */}
        <div className="grid grid-cols-2 gap-6 border-y border-war-800 py-4">
          {/* ATACANTE */}
          <div className="flex flex-col items-center gap-3">
            <div className="flex items-center gap-2">
              <PlayerAvatar avatarAssetId={attacker?.avatar_asset_id ?? null} color={attacker?.color ?? null} role={attacker?.role ?? 'player'} size="md" />
              <span className="font-bold text-sm" style={{ color: colorValue(attacker?.color) }}>
                {attacker?.nickname}
              </span>
            </div>

            <div className="flex flex-wrap justify-center gap-2">
              {sortedAttacker.map((val, idx) => {
                const defVal = sortedDefender[idx];
                const isWin = defVal !== undefined && val > defVal;
                const isLoss = defVal !== undefined && val <= defVal;

                return (
                  <Dice3D
                    key={`att-${idx}`}
                    value={val}
                    variant="attacker"
                    isRolling={isRolling}
                    isWinner={!isRolling && isWin}
                    isLoser={!isRolling && isLoss}
                    size="lg"
                  />
                );
              })}
            </div>
            <p className="text-xs font-semibold text-red-400">
              Bajas propias: <span className="text-sm font-bold">−{lastAttack.attackerLosses}</span>
            </p>
          </div>

          {/* DEFENSOR */}
          <div className="flex flex-col items-center gap-3">
            <div className="flex items-center gap-2">
              <PlayerAvatar avatarAssetId={defender?.avatar_asset_id ?? null} color={defender?.color ?? null} role={defender?.role ?? 'player'} size="md" />
              <span className="font-bold text-sm" style={{ color: colorValue(defender?.color) }}>
                {defender?.nickname}
              </span>
            </div>

            <div className="flex flex-wrap justify-center gap-2">
              {sortedDefender.map((val, idx) => {
                const attVal = sortedAttacker[idx];
                const isWin = attVal !== undefined && val >= attVal; // Empate favorece al defensor
                const isLoss = attVal !== undefined && val < attVal;

                return (
                  <Dice3D
                    key={`def-${idx}`}
                    value={val}
                    variant="defender"
                    isRolling={isRolling}
                    isWinner={!isRolling && isWin}
                    isLoser={!isRolling && isLoss}
                    size="lg"
                  />
                );
              })}
            </div>
            <p className="text-xs font-semibold text-sky-400">
              Bajas defensivas: <span className="text-sm font-bold">−{lastAttack.defenderLosses}</span>
            </p>
          </div>
        </div>

        {/* Resumen de comparaciones par a par */}
        {!isRolling && (
          <div className="mt-4 flex justify-center gap-4 text-xs font-medium text-stone-300">
            {Array.from({ length: pairsCount }).map((_, idx) => {
              const aVal = sortedAttacker[idx];
              const dVal = sortedDefender[idx];
              const attWon = aVal > dVal;

              return (
                <div
                  key={idx}
                  className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 ${
                    attWon ? 'border-emerald-500/60 bg-emerald-950/40 text-emerald-300' : 'border-red-500/60 bg-red-950/40 text-red-300'
                  }`}
                >
                  <span>Duelo #{idx + 1}:</span>
                  <strong className="font-bold">{aVal}</strong>
                  <span>vs</span>
                  <strong className="font-bold">{dVal}</strong>
                  <span>{attWon ? '➔ ⚔️ Gana Atacante' : '➔ 🛡️ Gana Defensor'}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
