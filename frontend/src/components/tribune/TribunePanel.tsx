import { useState } from 'react';
import { useGameStore } from '../../state/gameStore';
import { useConnectionStore } from '../../state/connectionStore';
import { useSessionStore } from '../../state/sessionStore';
import { colorValue } from '../../utils/playerColors';
import { wsClient } from '../../services/websocket/wsClient';
import { audioService } from '../../services/audio/AudioService';
import { AICommentatorPanel } from '../ai-commentator/AICommentatorPanel';
import { ChatPanel } from '../chat/ChatPanel';
import { SoundboardBar } from '../audio/SoundboardBar';
import { AudioControls } from '../audio/AudioControls';
import { territoryName as name } from '../../utils/territoryName';

/**
 * LA TRIBUNA: el dock lateral del prototipo. Cuando no es tu turno, acá está
 * la acción — batalla en vivo, apuesta de refuerzos, relator, diplomacia,
 * bardeo y chat. Nunca tapa el mapa y se puede plegar.
 */
export function TribunePanel() {
  const turn = useGameStore((s) => s.turn);
  const stage = useGameStore((s) => s.stage);
  const placementRemaining = useGameStore((s) => s.placementRemaining);
  const placementDone = useGameStore((s) => s.placementDone);
  const targetingMode = useGameStore((s) => s.targetingMode);
  const battle = useGameStore((s) => s.battle);
  const currentPlayerId = useGameStore((s) => s.currentPlayerId);
  const playerById = useGameStore((s) => s.playerById);
  const players = useGameStore((s) => s.players);
  const territories = useGameStore((s) => s.territories);
  const hasPactWith = useGameStore((s) => s.hasPactWith);
  const lastError = useGameStore((s) => s.lastError);
  const game = useGameStore((s) => s.game);
  const syncState = useConnectionStore((s) => s.syncState);
  const session = useSessionStore((s) => s.session);
  const [diplomacyOpen, setDiplomacyOpen] = useState(false);

  const currentId = currentPlayerId();
  const current = playerById(currentId);
  const myTurn = currentId === session?.playerId;
  const phase = turn?.phase ?? '';
  const inPlacement = stage === 'placement_1' || stage === 'placement_2';
  // el turno activo es el dato autoritativo: si hay turno en curso, la
  // partida corre aunque un status viejo diga otra cosa (p. ej. tras resync)
  const running = game?.status === 'running' || (stage === 'turns' && !!turn && game?.status !== 'finished' && game?.status !== 'paused');
  const combatants = players.filter(
    (p) => (p.role === 'player' || p.role === 'ai_player') && !p.eliminated,
  );
  const rivals = combatants.filter((p) => p.id !== session?.playerId);

  // instrucción concreta según estado (regla de claridad: qué puedo hacer)
  let turnTitle: string;
  let turnSub: string;
  if (syncState !== 'synced') {
    // design-review: la reconexión cambia el panel persistente, no solo un toast
    turnTitle = 'SINCRONIZANDO CON EL SERVIDOR…';
    turnSub = 'Recuperando el estado de la partida. Las acciones se desbloquean solas al terminar.';
  } else if (inPlacement) {
    turnTitle = `🪖 COLOCACIÓN INICIAL ${stage === 'placement_1' ? '(5 tropas)' : '(3 tropas)'}`;
    turnSub = placementRemaining > 0
      ? `Te quedan ${placementRemaining} por colocar — tocá tus países.`
      : `Listo. Esperando al resto (${placementDone.length}/${combatants.length}).`;
  } else if (!running) {
    turnTitle = game?.status === 'paused' ? '⏸️ PARTIDA PAUSADA' : 'ESPERANDO…';
    turnSub = game?.status === 'paused' ? 'El admin pausó la partida.' : '';
  } else if (myTurn) {
    turnTitle = `¡ES TU TURNO — ${phase === 'reinforcement' ? 'REFUERZOS 🪖' : phase === 'attack' ? 'ATAQUE ⚔️' : 'REAGRUPE 🛡️'}!`;
    turnSub = targetingMode === 'attack'
      ? 'Elegí el país enemigo resaltado para atacar.'
      : targetingMode === 'fortify'
        ? 'Elegí el país tuyo resaltado como destino.'
        : phase === 'reinforcement'
          ? `Tenés ${turn?.reinforcements_available ?? 0} tropas — tocá tus países para el menú radial.`
          : phase === 'attack'
            ? 'Tocá un país tuyo (borde dorado) y elegí ⚔️ Atacar.'
            : 'Tocá un país tuyo con tropas de sobra y elegí 🛡️ Fortificar.';
  } else {
    turnTitle = `TURNO DE ${current?.nickname?.toUpperCase() ?? '…'}`;
    turnSub = phase === 'reinforcement'
      ? `Está colocando refuerzos (le quedan ${turn?.reinforcements_available ?? 0}).`
      : phase === 'attack'
        ? 'Está eligiendo a quién atacar. Mirá la batalla acá abajo.'
        : 'Está reagrupando tropas.';
  }

  const wager = turn?.wager ?? 0;
  const canWager = myTurn && phase === 'reinforcement' && (turn?.reinforcements_available ?? 0) > 0;

  return (
    <aside
      className="flex min-h-0 flex-col gap-3 overflow-y-auto border-l-2 border-war-800 bg-war-900/95 p-3"
      data-testid="tribune-panel"
      aria-label="La Tribuna"
    >
      {/* estado del turno */}
      <div
        className="rounded-lg border-l-4 bg-war-950 p-3 transition-colors"
        style={{ borderLeftColor: colorValue(current?.color) }}
        data-testid="tribune-turn-box"
      >
        <p className="text-[10px] font-bold tracking-widest text-stone-500">ESTADO DEL TURNO</p>
        <p className="text-sm font-bold text-stone-100">{turnTitle}</p>
        <p className="mt-0.5 text-xs text-stone-400">{turnSub}</p>
        {myTurn && running && !inPlacement && syncState === 'synced' && (
          <div className="mt-2 flex gap-2">
            {phase !== 'fortify' ? (
              <button
                onClick={() => { audioService.unlock(); wsClient.send({ type: 'turn.next_phase' }); }}
                disabled={phase === 'reinforcement' && (turn?.reinforcements_available ?? 0) > 0}
                title={phase === 'reinforcement' && (turn?.reinforcements_available ?? 0) > 0 ? 'Primero colocá todos tus refuerzos' : ''}
                data-testid="next-phase"
                className="flex-1 rounded-lg bg-gold-500 px-3 py-1.5 text-xs font-bold text-war-950 hover:bg-gold-400 disabled:opacity-40"
              >
                {phase === 'reinforcement' ? 'Pasar a Ataque ⚔️' : 'Pasar a Reagrupe 🛡️'}
              </button>
            ) : null}
            <button
              onClick={() => { audioService.unlock(); wsClient.send({ type: 'turn.end' }); }}
              data-testid="end-turn"
              className="flex-1 rounded-lg border border-war-600 px-3 py-1.5 text-xs font-bold hover:border-gold-500"
            >
              Terminar turno ⌛
            </button>
          </div>
        )}
        {lastError && Date.now() - lastError.at < 6000 && (
          <p role="alert" className="mt-2 rounded bg-red-950/60 px-2 py-1 text-xs text-red-300">
            {lastError.message}
          </p>
        )}
      </div>

      {/* LA TRIBUNA: batalla en vivo + apuesta */}
      <div className="rounded-lg border border-war-700 bg-war-950 p-3" data-testid="tribune-market">
        <p className="text-[10px] font-bold tracking-widest text-stone-500">🏟️ LA TRIBUNA</p>

        {battle && battle.rounds.length > 0 ? (
          <p className="mt-1 text-xs text-stone-200">
            ⚔️ <strong className="capitalize">{name(battle.sourceId)}</strong> ataca{' '}
            <strong className="capitalize">{name(battle.targetId)}</strong>
            {battle.conquered ? ' — ¡cayó! 🚩' : ` (${battle.rounds.length} ronda${battle.rounds.length !== 1 ? 's' : ''})`}
          </p>
        ) : (
          <p className="mt-1 text-xs text-stone-500">Sin batallas en curso.</p>
        )}

        {/* apuesta real del turno: refuerzos arriesgados (backend autoritativo) */}
        <div className="mt-2 rounded-md border border-gold-600/40 bg-war-900 p-2">
          <p className="text-[11px] font-bold text-gold-400">🎰 APUESTA DE REFUERZOS</p>
          <p className="text-[10px] text-stone-400">
            Arriesgá refuerzos: si conquistás al menos un país este turno, vuelven al doble el próximo.
          </p>
          {wager > 0 && (
            <p className="mt-1 text-xs font-bold text-amber-300" data-testid="wager-current">
              En juego: {wager} tropa{wager !== 1 ? 's' : ''} → paga {wager * 2}
            </p>
          )}
          {canWager ? (
            <div className="mt-1.5 flex gap-1.5">
              {[1, 3].map((n) => (
                <button
                  key={n}
                  disabled={(turn?.reinforcements_available ?? 0) < n}
                  onClick={() => { audioService.unlock(); wsClient.send({ type: 'turn.wager', payload: { amount: n } }); }}
                  data-testid={`wager-${n}`}
                  className="flex-1 rounded bg-gold-500/90 px-2 py-1 text-[11px] font-bold text-war-950 hover:bg-gold-400 disabled:opacity-30"
                >
                  Arriesgar +{n}
                </button>
              ))}
            </div>
          ) : (
            <p className="mt-1 text-[10px] text-stone-500">
              {myTurn ? 'Solo se apuesta en tu fase de refuerzos.' : 'Solo el jugador de turno arriesga refuerzos.'}
            </p>
          )}
        </div>

        {/* mercado de espectadores: honesto sobre su estado */}
        <div className="mt-2 rounded-md border border-war-700 bg-war-900 p-2 opacity-80">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-bold text-stone-300">📊 MERCADO DE ESPECTADORES</p>
            <span className="rounded bg-war-700 px-1.5 py-0.5 text-[9px] text-stone-300">MODO CLÁSICO</span>
          </div>
          <div className="mt-1 flex gap-1.5">
            <button disabled className="flex-1 cursor-not-allowed rounded border border-war-700 px-2 py-1 text-[11px] text-stone-500">
              APOSTAR SÍ
            </button>
            <button disabled className="flex-1 cursor-not-allowed rounded border border-war-700 px-2 py-1 text-[11px] text-stone-500">
              APOSTAR NO
            </button>
          </div>
          <p className="mt-1 text-[10px] text-stone-500">
            No elegible todavía: el ledger de Monedas LOPDA (virtuales, sin valor real) se está
            integrando en el servidor. Mientras, corre la apuesta de refuerzos de arriba.
          </p>
        </div>
      </div>

      {/* relator */}
      <AICommentatorPanel />

      {/* diplomacia */}
      <div className="rounded-lg border border-war-700 bg-war-950 p-3" data-testid="tribune-diplomacy">
        <button
          onClick={() => setDiplomacyOpen((o) => !o)}
          className="flex w-full items-center justify-between text-left"
        >
          <p className="text-[10px] font-bold tracking-widest text-stone-500">🤝 DIPLOMACIA</p>
          <span className="text-xs text-stone-500">{diplomacyOpen ? '▾' : '▸'}</span>
        </button>
        {diplomacyOpen && session?.role !== 'spectator' && (
          <ul className="mt-2 space-y-1.5">
            {rivals.map((p) => {
              const allied = hasPactWith(p.id);
              const troops = Object.values(territories)
                .filter((t) => t.owner_player_id === p.id)
                .reduce((a, t) => a + t.armies, 0);
              return (
                <li key={p.id} className="flex items-center gap-2 text-xs">
                  <span className="w-20 truncate font-semibold" style={{ color: colorValue(p.color) }}>{p.nickname}</span>
                  <span className="text-[10px] text-stone-500">🪖{troops}</span>
                  {allied ? (
                    <button
                      onClick={() => wsClient.send({ type: 'pact.break', payload: { target_player_id: p.id } })}
                      className="ml-auto rounded border border-red-800 px-1.5 py-0.5 text-[10px] text-red-300 hover:border-red-500"
                    >
                      🗡️ romper
                    </button>
                  ) : (
                    <button
                      onClick={() => wsClient.send({ type: 'pact.propose', payload: { target_player_id: p.id } })}
                      className="ml-auto rounded border border-war-700 px-1.5 py-0.5 text-[10px] hover:border-gold-500"
                    >
                      🤝 pacto
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {/* bardeo + chat + audio */}
      <div className="rounded-lg border border-war-700 bg-war-950 p-3">
        <p className="mb-1.5 text-[10px] font-bold tracking-widest text-stone-500">🎙️ BARDEO RÁPIDO</p>
        <SoundboardBar />
      </div>
      <ChatPanel compact />
      <AudioControls />
    </aside>
  );
}
