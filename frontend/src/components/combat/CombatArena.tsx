import { useEffect, useRef, useState } from 'react';
import { useGameStore } from '../../state/gameStore';
import { useSessionStore } from '../../state/sessionStore';
import { colorValue } from '../../utils/playerColors';
import { wsClient } from '../../services/websocket/wsClient';
import { Dice3D } from '../dice/Dice3D';
import { territoryName as name } from '../../utils/territoryName';

type Speed = '1x' | '2x' | 'instant';
const SPEED_MS: Record<Speed, number> = { '1x': 1200, '2x': 400, instant: 0 };
const SPEED_KEY = 'teg.combatSpeed';

/**
 * Arena de Combate (combat-design.md): desglose matemático transparente.
 * El backend tira los dados; acá SOLO se anima y explica ese resultado.
 */
export function CombatArena() {
  const battle = useGameStore((s) => s.battle);
  const territories = useGameStore((s) => s.territories);
  const playerById = useGameStore((s) => s.playerById);
  const closeBattle = useGameStore((s) => s.closeBattle);
  const setTargeting = useGameStore((s) => s.setTargetingMode);
  const setSelectedSource = useGameStore((s) => s.setSelectedSourceTerritory);
  const setSelectedTarget = useGameStore((s) => s.setSelectedTargetTerritory);
  const session = useSessionStore((s) => s.session);

  const [speed, setSpeed] = useState<Speed>(() => (localStorage.getItem(SPEED_KEY) as Speed) || '1x');
  const [rolling, setRolling] = useState(false);
  const lastRoundCount = useRef(0);
  const cardRef = useRef<HTMLDivElement>(null);

  const reducedMotion = typeof window !== 'undefined'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const rollMs = reducedMotion ? 0 : SPEED_MS[speed];

  // animación de tirada al llegar una ronda nueva
  useEffect(() => {
    const n = battle?.rounds.length ?? 0;
    if (n > lastRoundCount.current && rollMs > 0) {
      setRolling(true);
      const t = window.setTimeout(() => setRolling(false), rollMs + 80);
      lastRoundCount.current = n;
      return () => window.clearTimeout(t);
    }
    lastRoundCount.current = n;
  }, [battle?.rounds.length, rollMs]);

  useEffect(() => {
    if (battle?.open) cardRef.current?.focus();
  }, [battle?.open]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') stop();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!battle || !battle.open || battle.rounds.length === 0) return null;

  const attacker = playerById(battle.attackerId);
  const defender = playerById(battle.defenderId);
  const last = battle.rounds[battle.rounds.length - 1];
  const attackerNow = last.attackerAfter ?? territories[battle.sourceId]?.armies ?? 0;
  const defenderNow = battle.conquered ? 0 : (last.defenderAfter ?? territories[battle.targetId]?.armies ?? 0);
  const totalAttLoss = battle.rounds.reduce((a, r) => a + r.attackerLosses, 0);
  const totalDefLoss = battle.rounds.reduce((a, r) => a + r.defenderLosses, 0);
  const iAmAttacker = battle.attackerId === session?.playerId;
  const canContinue = iAmAttacker && !battle.conquered && attackerNow > 1 && defenderNow > 0;

  function stop() {
    closeBattle();
    setTargeting(null);
    setSelectedSource(null);
    setSelectedTarget(null);
  }

  function attackAgain() {
    wsClient.send({
      type: 'attack',
      payload: {
        source_territory_id: battle!.sourceId,
        target_territory_id: battle!.targetId,
        attacker_dice: 3,
      },
    });
  }

  function pickSpeed(s: Speed) {
    setSpeed(s);
    localStorage.setItem(SPEED_KEY, s);
  }

  const dieStyle = rollMs > 0 ? ({ ['--die-roll-ms' as string]: `${rollMs}ms` }) : undefined;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-war-950/85 p-4 backdrop-blur-sm" data-testid="combat-arena">
      <div
        ref={cardRef}
        tabIndex={-1}
        className="max-h-[92vh] w-[820px] max-w-[96vw] overflow-y-auto rounded-xl border-2 border-gold-600 bg-war-950 p-5 shadow-2xl outline-none"
      >
        <div className="mb-3 flex items-center justify-between border-b border-war-700 pb-2">
          <h3 className="font-display text-lg font-bold text-gold-400">⚔️ ARENA DE COMBATE</h3>
          <button onClick={stop} className="rounded-lg border border-war-700 px-3 py-1 text-sm hover:border-gold-500" title="Cerrar (Esc)">
            ✕ {iAmAttacker && !battle.conquered ? 'Detener' : 'Cerrar'}
          </button>
        </div>

        {/* cabecera: bandos, tropas y explicación de dados */}
        <div className="mb-3 grid grid-cols-2 gap-3 rounded-lg bg-war-800 p-3">
          <div>
            <strong className="capitalize" style={{ color: colorValue(attacker?.color) }}>
              {name(battle.sourceId)} — {attacker?.nickname ?? '???'} (ataca)
            </strong>
            <p className="text-xs text-stone-400">
              Inició con <strong>{battle.attackerInitial}</strong> · ahora <strong className="text-stone-200">{attackerNow}</strong> · tiró {last.attackerDice.length} dado{last.attackerDice.length !== 1 ? 's' : ''}
            </p>
            <p className="text-[10px] text-stone-500">
              Regla: min(tropas − 1, 3) → con {battle.attackerInitial} tropas, {Math.min(Math.max(battle.attackerInitial - 1, 1), 3)} dados
            </p>
          </div>
          <div>
            <strong className="capitalize" style={{ color: colorValue(defender?.color) }}>
              {name(battle.targetId)} — {defender?.nickname ?? '???'} (defiende)
            </strong>
            <p className="text-xs text-stone-400">
              Inició con <strong>{battle.defenderInitial}</strong> · ahora <strong className="text-stone-200">{defenderNow}</strong> · tiró {last.defenderDice.length} dado{last.defenderDice.length !== 1 ? 's' : ''}
            </p>
            <p className="text-[10px] text-stone-500">
              Regla: min(tropas, 3) → defendió con {last.defenderDice.length} dado{last.defenderDice.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>

        {/* última tirada: dados con física visual */}
        <div className="mb-3 flex items-center justify-center gap-6 rounded-lg bg-war-900 py-3">
          <div className="flex gap-2">
            {last.attackerDice.map((d, i) => (
              <span key={`${battle.rounds.length}-a-${i}`} className={rollMs > 0 ? 'arena-die' : ''} style={dieStyle}>
                <Dice3D value={d} variant="attacker" size="md" />
              </span>
            ))}
          </div>
          <span className="font-display text-xl font-black text-stone-500">VS</span>
          <div className="flex gap-2">
            {last.defenderDice.map((d, i) => (
              <span key={`${battle.rounds.length}-d-${i}`} className={rollMs > 0 ? 'arena-die' : ''} style={dieStyle}>
                <Dice3D value={d} variant="defender" size="md" />
              </span>
            ))}
          </div>
        </div>

        {/* desglose de parejas, con la regla del empate explícita */}
        {!rolling && (
          <div data-testid="pair-breakdown">
            {last.comparisons.map((c, i) => {
              const attackerWins = c.attacker > c.defender;
              const tie = c.attacker === c.defender;
              return (
                <div key={i} className="mb-1.5 flex flex-wrap items-center justify-between gap-2 rounded-md bg-war-800 px-3 py-1.5 text-sm">
                  <span>
                    Pareja {i + 1}:{' '}
                    <span className="inline-flex h-6 w-6 items-center justify-center rounded bg-red-600 text-xs font-bold text-white">{c.attacker}</span>
                    {' vs '}
                    <span className="inline-flex h-6 w-6 items-center justify-center rounded bg-sky-600 text-xs font-bold text-white">{c.defender}</span>
                  </span>
                  <strong className={attackerWins ? 'text-emerald-400' : 'text-sky-400'}>
                    {attackerWins
                      ? `⚔️ gana atacante (${c.attacker} > ${c.defender}) → defensor pierde 1`
                      : tie
                        ? '🛡️ EMPATE: la regla del TEG favorece al defensor → atacante pierde 1'
                        : `🛡️ gana defensor (${c.defender} > ${c.attacker}) → atacante pierde 1`}
                  </strong>
                </div>
              );
            })}
          </div>
        )}

        {/* resumen acumulado reconstruible sin logs */}
        <div className="mt-3 rounded-md border border-war-600 bg-war-950 p-3 text-sm" data-testid="battle-summary">
          <strong className="text-stone-200">RESUMEN ACUMULADO ({battle.rounds.length} ronda{battle.rounds.length !== 1 ? 's' : ''}):</strong>
          <ul className="mt-1 max-h-24 overflow-y-auto text-xs text-stone-400">
            {battle.rounds.map((r, i) => (
              <li key={i}>
                Ronda {i + 1}: atacante perdió {r.attackerLosses}, defensor perdió {r.defenderLosses}
              </li>
            ))}
          </ul>
          <p className="mt-1.5 text-xs text-stone-300">
            <span className="capitalize">{name(battle.sourceId)}</span>: {battle.attackerInitial} → {attackerNow} (−{totalAttLoss}) ·{' '}
            <span className="capitalize">{name(battle.targetId)}</span>: {battle.defenderInitial} → {defenderNow} (−{totalDefLoss})
            {battle.conquered && <strong className="text-gold-400"> — ¡CONQUISTADO!</strong>}
          </p>
        </div>

        {battle.conquered && (
          <div className="mt-3 rounded-lg border border-gold-500 bg-gold-950/40 p-3 text-center" data-testid="conquest-banner">
            <p className="font-display text-xl font-black text-gold-400">🚩 ¡TERRITORIO CONQUISTADO!</p>
            <p className="text-xs text-stone-300">Las tropas atacantes avanzaron automáticamente a ocuparlo.</p>
          </div>
        )}

        {/* controles: velocidad + seguir/detener */}
        <div className="mt-4 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-1 text-xs text-stone-400">
            Velocidad:
            {(['1x', '2x', 'instant'] as Speed[]).map((s) => (
              <button
                key={s}
                onClick={() => pickSpeed(s)}
                className={`rounded px-2 py-0.5 text-[11px] ${speed === s ? 'bg-gold-500 font-bold text-war-950' : 'border border-war-700 hover:border-gold-500'}`}
              >
                {s === 'instant' ? 'Instantáneo ⚡' : s}
              </button>
            ))}
            {reducedMotion && <span className="ml-1 text-[10px] text-stone-500">(animación reducida activa)</span>}
          </div>
          <div className="flex gap-2">
            {iAmAttacker && !battle.conquered && (
              <button
                onClick={attackAgain}
                disabled={!canContinue || rolling}
                data-testid="attack-again"
                title={!canContinue ? 'Necesitás al menos 2 tropas en el origen para seguir' : ''}
                className="rounded-lg bg-red-600 px-4 py-1.5 text-sm font-bold text-white hover:bg-red-500 disabled:opacity-40"
              >
                ⚔️ Seguir atacando
              </button>
            )}
            <button onClick={stop} data-testid="stop-attack" className="rounded-lg border border-war-600 px-4 py-1.5 text-sm hover:border-gold-500">
              {battle.conquered || !iAmAttacker ? 'Cerrar' : '🛑 Detener'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
