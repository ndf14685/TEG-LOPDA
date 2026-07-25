import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { wsClient } from '../services/websocket/wsClient';
import { bindWsToStores } from '../services/websocket/bindStores';
import { useSessionStore } from '../state/sessionStore';
import { useGameStore } from '../state/gameStore';
import { useConnectionStore } from '../state/connectionStore';
import { MapPanel } from '../components/map/MapPanel';
import { TurnPhaseBar } from '../components/game/TurnPhaseBar';
import { TopHud } from '../components/hud/TopHud';
import { TurnBanner } from '../components/hud/TurnBanner';
import { TribunePanel } from '../components/tribune/TribunePanel';
import { CombatArena } from '../components/combat/CombatArena';
import { ConnectionBanner } from '../components/ConnectionBanner';
import { colorValue } from '../utils/playerColors';
import { PostGameModal } from '../components/game/PostGameModal';
import { WagerToast } from '../components/game/WagerToast';

/**
 * Pantalla de juego productiva (layout del prototipo aprobado): HUD superior
 * de jugadores, mapa protagonista con interacción directa y La Tribuna como
 * dock lateral plegable. La viñeta ambiental toma el color del jugador activo.
 */
export function GamePage() {
  const { code = '' } = useParams();
  const navigate = useNavigate();
  const session = useSessionStore((s) => s.session);
  const restore = useSessionStore((s) => s.restore);
  const game = useGameStore((s) => s.game);
  const stage = useGameStore((s) => s.stage);
  const pactProposalFrom = useGameStore((s) => s.pactProposalFrom);
  const playerById = useGameStore((s) => s.playerById);
  const currentPlayerId = useGameStore((s) => s.currentPlayerId);
  const syncState = useConnectionStore((s) => s.syncState);
  const [tribuneOpen, setTribuneOpen] = useState(true);

  useEffect(() => {
    if ((!session || session.code !== code) && !restore(code)) navigate('/');
  }, [session, code, restore, navigate]);

  useEffect(() => {
    if (!session || session.code !== code) return;
    bindWsToStores();
    wsClient.connect(code, session.token);
  }, [session, code]);

  if (!session) return null;

  const currentId = currentPlayerId();
  const current = playerById(currentId);
  const myTurn = currentId === session.playerId;
  const running = game?.status === 'running';
  const ambientColor = current ? colorValue(current.color) : '#d97706';

  return (
    <main className="flex h-screen flex-col overflow-hidden bg-war-950" data-testid="game-board">
      <ConnectionBanner />
      <TopHud />
      <TurnBanner />

      {/* propuesta de pacto entrante */}
      {pactProposalFrom && (
        <div className="fixed left-1/2 top-16 z-40 flex -translate-x-1/2 items-center gap-3 rounded-xl border border-gold-500/60 bg-war-900/95 px-4 py-2.5 shadow-2xl backdrop-blur-md" data-testid="pact-proposal">
          <span className="text-sm text-stone-200">
            <strong style={{ color: colorValue(playerById(pactProposalFrom)?.color) }}>
              {playerById(pactProposalFrom)?.nickname ?? '???'}
            </strong>{' '}
            te propone un pacto de no agresión
          </span>
          <button
            onClick={() => wsClient.send({ type: 'pact.respond', payload: { accept: true } })}
            className="rounded-lg bg-gold-500 px-3 py-1 text-xs font-bold text-war-950 hover:bg-gold-400"
          >
            Aceptar
          </button>
          <button
            onClick={() => wsClient.send({ type: 'pact.respond', payload: { accept: false } })}
            className="rounded-lg border border-war-600 px-3 py-1 text-xs text-stone-300 hover:border-red-500"
          >
            Rechazar
          </button>
        </div>
      )}

      <div className={`grid min-h-0 flex-1 grid-cols-1 ${tribuneOpen ? 'lg:grid-cols-[1fr_360px]' : ''}`}>
        {/* mapa protagonista */}
        <section className="relative flex min-h-0 flex-col">
          <div className="px-2 pt-2">
            {stage !== 'placement_1' && stage !== 'placement_2' && <TurnPhaseBar />}
          </div>
          <div className="relative min-h-0 flex-1 overflow-hidden p-2">
            <MapPanel />
            {/* viñeta ambiental del jugador activo */}
            <div
              className={`ambient-vignette ${running && current ? 'active' : ''}`}
              style={{
                boxShadow: myTurn
                  ? `inset 0 0 110px ${ambientColor}55`
                  : `inset 0 0 70px ${ambientColor}33`,
              }}
              aria-hidden
            />
            {game?.status === 'paused' && (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-war-950/70">
                <p className="rounded-lg bg-war-800 px-4 py-2 text-sm">⏸️ Partida pausada por el admin</p>
              </div>
            )}
            {syncState !== 'synced' && (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-war-950/70">
                <p className="rounded-lg bg-war-800 px-4 py-2 text-sm">📡 Sincronizando — acciones bloqueadas un instante</p>
              </div>
            )}
          </div>

          {/* toggle de La Tribuna (siempre accesible, nunca tapa el mapa) */}
          <button
            onClick={() => setTribuneOpen((o) => !o)}
            data-testid="tribune-toggle"
            className="absolute right-2 top-2 z-20 rounded-lg border border-war-600 bg-war-900/90 px-2.5 py-1 text-xs font-bold text-stone-300 backdrop-blur-sm hover:border-gold-500"
            title={tribuneOpen ? 'Plegar La Tribuna' : 'Abrir La Tribuna'}
          >
            {tribuneOpen ? 'LA TRIBUNA ›' : '‹ LA TRIBUNA'}
          </button>
        </section>

        {/* La Tribuna */}
        {tribuneOpen && <TribunePanel />}
      </div>

      <CombatArena />
      <WagerToast />
      <PostGameModal />
    </main>
  );
}
