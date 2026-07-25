import { useEffect } from 'react';
import { useGameStore } from '../../state/gameStore';
import { wsClient } from '../../services/websocket/wsClient';
import { audioService } from '../../services/audio/AudioService';
import { territoryName } from '../../utils/territoryName';

/**
 * Menú radial táctico (interaction-rules.md): toda acción sale de un gesto
 * directo sobre el territorio. Sin selects, sin inputs numéricos.
 */
export function RadialMenu() {
  const menu = useGameStore((s) => s.radialMenu);
  const setMenu = useGameStore((s) => s.setRadialMenu);
  const stage = useGameStore((s) => s.stage);
  const turn = useGameStore((s) => s.turn);
  const youId = useGameStore((s) => s.youId);
  const territories = useGameStore((s) => s.territories);
  const placementRemaining = useGameStore((s) => s.placementRemaining);
  const optimisticPlace = useGameStore((s) => s.optimisticPlace);
  const setSelectedSource = useGameStore((s) => s.setSelectedSourceTerritory);
  const setSelectedTarget = useGameStore((s) => s.setSelectedTargetTerritory);
  const setTargeting = useGameStore((s) => s.setTargetingMode);
  const fortifyPicker = useGameStore((s) => s.fortifyPicker);
  const setFortifyPicker = useGameStore((s) => s.setFortifyPicker);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setMenu(null);
        setFortifyPicker(null);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [setMenu, setFortifyPicker]);

  // --- selector de cantidad para reagrupar (destino ya elegido) ---
  if (fortifyPicker && menu) {
    const maxMove = Math.max(1, (territories[fortifyPicker.source]?.armies ?? 1) - 1);
    const sendFortify = (count: number) => {
      audioService.unlock();
      wsClient.send({
        type: 'turn.fortify',
        payload: {
          source_territory_id: fortifyPicker.source,
          target_territory_id: fortifyPicker.target,
          count: Math.max(1, Math.min(count, maxMove)),
        },
      });
      audioService.playGameSound('audio.ui.reinforce', [520, 780]);
      setFortifyPicker(null);
      setMenu(null);
      setSelectedSource(null);
      setSelectedTarget(null);
      setTargeting(null);
    };
    return (
      <div
        className="radial-menu"
        style={{ left: menu.x, top: menu.y }}
        role="menu"
        aria-label={`Mover tropas hacia ${territoryName(fortifyPicker.target)}`}
        onClick={(e) => e.stopPropagation()}
      >
        <span className="radial-title">🛡️ mover a {territoryName(fortifyPicker.target)}</span>
        <button className="radial-btn bg-sky-600" onClick={() => sendFortify(1)}>+1</button>
        {maxMove >= 3 && <button className="radial-btn bg-sky-700" onClick={() => sendFortify(3)}>+3</button>}
        {maxMove > 1 && (
          <button className="radial-btn bg-sky-800" onClick={() => sendFortify(maxMove)}>
            MÁX ({maxMove})
          </button>
        )}
        <button className="radial-btn bg-war-700" onClick={() => { setFortifyPicker(null); setMenu(null); }}>✕</button>
      </div>
    );
  }

  if (!menu) return null;
  const tid = menu.territoryId;
  const t = territories[tid];
  const mine = t?.owner_player_id === youId;
  const myTurn = turn && turn.order[turn.index] === youId;
  const name = territoryName(tid);

  const close = () => setMenu(null);

  // --- colocación inicial: +1 / +3 / MAX del pool oculto ---
  if ((stage === 'placement_1' || stage === 'placement_2') && mine && placementRemaining > 0) {
    const place = (count: number) => {
      const n = Math.min(count, placementRemaining);
      for (let i = 0; i < n; i++) optimisticPlace(tid);
      audioService.unlock();
      wsClient.send({ type: 'placement.place', payload: { territory_id: tid, count: n } });
      audioService.playGameSound('audio.ui.reinforce', [520, 780]);
      close();
    };
    return (
      <div className="radial-menu" style={{ left: menu.x, top: menu.y }} role="menu" aria-label={`Colocar en ${name}`} onClick={(e) => e.stopPropagation()}>
        <span className="radial-title">🪖 {name}</span>
        <button className="radial-btn bg-emerald-600" onClick={() => place(1)}>+1</button>
        {placementRemaining >= 3 && <button className="radial-btn bg-emerald-700" onClick={() => place(3)}>+3</button>}
        {placementRemaining > 1 && (
          <button className="radial-btn bg-emerald-800" onClick={() => place(placementRemaining)}>
            MÁX ({placementRemaining})
          </button>
        )}
        <button className="radial-btn bg-war-700" onClick={close}>✕</button>
      </div>
    );
  }

  if (!myTurn || !mine || stage !== 'turns') return null;

  const phase = turn?.phase ?? 'attack';

  // --- refuerzos: +1 / +3 / MAX ---
  if (phase === 'reinforcement') {
    const available = turn?.reinforcements_available ?? 0;
    if (available <= 0) return null;
    const reinforce = (count: number) => {
      audioService.unlock();
      wsClient.send({
        type: 'turn.place_reinforcement',
        payload: { territory_id: tid, count: Math.min(count, available) },
      });
      audioService.playGameSound('audio.ui.reinforce', [520, 780]);
      close();
    };
    return (
      <div className="radial-menu" style={{ left: menu.x, top: menu.y }} role="menu" aria-label={`Reforzar ${name}`} onClick={(e) => e.stopPropagation()}>
        <span className="radial-title">🪖 {name}</span>
        <button className="radial-btn bg-emerald-600" onClick={() => reinforce(1)}>+1</button>
        {available >= 3 && <button className="radial-btn bg-emerald-700" onClick={() => reinforce(3)}>+3</button>}
        {available > 1 && (
          <button className="radial-btn bg-emerald-800" onClick={() => reinforce(available)}>
            MÁX ({available})
          </button>
        )}
        <button className="radial-btn bg-war-700" onClick={close}>✕</button>
      </div>
    );
  }

  // --- ataque / reagrupamiento: activa el modo de puntería ---
  const canAct = (t?.armies ?? 0) > 1;
  return (
    <div className="radial-menu" style={{ left: menu.x, top: menu.y }} role="menu" aria-label={`Acciones de ${name}`} onClick={(e) => e.stopPropagation()}>
      <span className="radial-title">{name} ({t?.armies ?? 0})</span>
      {phase === 'attack' && (
        <button
          className="radial-btn bg-red-600"
          disabled={!canAct}
          title={canAct ? 'Elegí después el país enemigo' : 'Necesitás al menos 2 tropas para atacar'}
          onClick={() => {
            setSelectedSource(tid);
            setSelectedTarget(null);
            setTargeting('attack');
            close();
          }}
        >
          ⚔️ Atacar
        </button>
      )}
      {phase === 'fortify' && (
        <button
          className="radial-btn bg-sky-600"
          disabled={!canAct}
          title={canAct ? 'Elegí después el país propio destino' : 'Necesitás al menos 2 tropas para mover'}
          onClick={() => {
            setSelectedSource(tid);
            setSelectedTarget(null);
            setTargeting('fortify');
            close();
          }}
        >
          🛡️ Fortificar
        </button>
      )}
      {phase === 'attack' && !canAct && (
        <span className="radial-hint">Con 1 tropa no se ataca: reforzalo el próximo turno</span>
      )}
      <button className="radial-btn bg-war-700" onClick={close}>✕</button>
    </div>
  );
}
