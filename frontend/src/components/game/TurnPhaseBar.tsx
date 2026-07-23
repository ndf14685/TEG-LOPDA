import { useGameStore } from '../../state/gameStore';
import { useSessionStore } from '../../state/sessionStore';
import { wsClient } from '../../services/websocket/wsClient';
import { audioService } from '../../services/audio/AudioService';
import { CountryCardsModal } from '../cards/CountryCardsModal';
import { SecretObjectiveModal } from '../objectives/SecretObjectiveModal';

export function TurnPhaseBar() {
  const turn = useGameStore((s) => s.turn);
  const session = useSessionStore((s) => s.session);
  const currentPlayerId = useGameStore((s) => s.currentPlayerId);
  const currentId = currentPlayerId();
  const myTurn = currentId === session?.playerId;

  if (!turn) return null;

  const currentPhase = turn.phase ?? 'attack';
  const availableReinforcements = turn.reinforcements_available ?? 0;

  function advancePhase() {
    audioService.unlock();
    wsClient.send({ type: 'turn.next_phase' });
  }

  const phaseStep = currentPhase === 'reinforcement' ? 1 : currentPhase === 'attack' ? 2 : 3;

  return (
    <div className="flex flex-col gap-2 rounded-xl border border-war-700 bg-war-900/90 p-3 shadow-lg backdrop-blur-md">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <h3 className="text-xs font-semibold tracking-wider text-stone-400">FASE DEL TURNO #{turn.turn_number}</h3>
          <SecretObjectiveModal />
          <CountryCardsModal />
        </div>
        {myTurn && (
          <button
            onClick={advancePhase}
            className="rounded-lg bg-gold-500/90 px-3 py-1 text-xs font-bold text-war-950 transition hover:bg-gold-400"
          >
            {currentPhase === 'reinforcement'
              ? 'Pasar a Ataque ⚔️ ➔'
              : currentPhase === 'attack'
                ? 'Pasar a Reagrupar 🛡️ ➔'
                : 'Fin de Turno ⌛ ➔'}
          </button>
        )}
      </div>

      {/* Indicador de 3 pasos de Fase */}
      <div className="grid grid-cols-3 gap-2">
        {/* PASO 1: REFUERZOS */}
        <div
          className={`flex items-center gap-2 rounded-lg border p-2 text-xs transition ${
            phaseStep === 1
              ? 'border-amber-400 bg-amber-950/60 font-bold text-amber-300 ring-2 ring-amber-400/40'
              : phaseStep > 1
                ? 'border-emerald-800 bg-emerald-950/30 text-emerald-400'
                : 'border-war-800 bg-war-950/40 text-stone-500'
          }`}
        >
          <span className="text-sm">🪖</span>
          <div className="truncate">
            <p className="leading-none">1. Refuerzos</p>
            {phaseStep === 1 && myTurn && (
              <p className="mt-0.5 text-[10px] text-amber-200">
                Disponibles: <strong className="text-gold-400">{availableReinforcements}</strong>
              </p>
            )}
          </div>
        </div>

        {/* PASO 2: ATAQUE */}
        <div
          className={`flex items-center gap-2 rounded-lg border p-2 text-xs transition ${
            phaseStep === 2
              ? 'border-red-500 bg-red-950/60 font-bold text-red-300 ring-2 ring-red-500/40'
              : phaseStep > 2
                ? 'border-emerald-800 bg-emerald-950/30 text-emerald-400'
                : 'border-war-800 bg-war-950/40 text-stone-500'
          }`}
        >
          <span className="text-sm">⚔️</span>
          <div className="truncate">
            <p className="leading-none">2. Ataque</p>
            {phaseStep === 2 && myTurn && <p className="mt-0.5 text-[10px] text-red-200">Seleccioná origen y objetivo</p>}
          </div>
        </div>

        {/* PASO 3: REAGRUPAMIENTO */}
        <div
          className={`flex items-center gap-2 rounded-lg border p-2 text-xs transition ${
            phaseStep === 3
              ? 'border-sky-400 bg-sky-950/60 font-bold text-sky-300 ring-2 ring-sky-400/40'
              : 'border-war-800 bg-war-950/40 text-stone-500'
          }`}
        >
          <span className="text-sm">🛡️</span>
          <div className="truncate">
            <p className="leading-none">3. Reagrupar</p>
            {phaseStep === 3 && myTurn && <p className="mt-0.5 text-[10px] text-sky-200">Mover tropas propias</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
