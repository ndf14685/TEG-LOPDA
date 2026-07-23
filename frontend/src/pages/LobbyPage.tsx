import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { wsClient } from '../services/websocket/wsClient';
import { bindWsToStores } from '../services/websocket/bindStores';
import { useSessionStore } from '../state/sessionStore';
import { useGameStore } from '../state/gameStore';
import { PlayerCard } from '../components/players/PlayerCard';
import { ChatPanel } from '../components/chat/ChatPanel';
import { ConnectionBanner } from '../components/ConnectionBanner';
import { api } from '../services/api/apiClient';
import { audioService } from '../services/audio/AudioService';

const COUNTDOWN_SECONDS = 3;

export function LobbyPage() {
  const { code = '' } = useParams();
  const navigate = useNavigate();
  const session = useSessionStore((s) => s.session);
  const adminToken = useSessionStore((s) => s.adminToken);
  const restore = useSessionStore((s) => s.restore);
  const game = useGameStore((s) => s.game);
  const players = useGameStore((s) => s.players);
  const gameStartedAt = useGameStore((s) => s.gameStartedAt);
  const [ready, setReady] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState<number | null>(null);
  const [startError, setStartError] = useState<string | null>(null);

  useEffect(() => {
    if ((!session || session.code !== code) && !restore(code)) navigate('/');
  }, [session, code, restore, navigate]);

  useEffect(() => {
    if (!session || session.code !== code) return;
    bindWsToStores();
    wsClient.connect(code, session.token);
  }, [session, code]);

  // game.started => countdown local dramático y al tablero
  useEffect(() => {
    if (!gameStartedAt) return;
    audioService.unlock();
    let remaining = COUNTDOWN_SECONDS;
    setSecondsLeft(remaining);
    const interval = setInterval(() => {
      remaining -= 1;
      if (remaining <= 0) {
        clearInterval(interval);
        navigate(`/game/${code}`);
      } else {
        setSecondsLeft(remaining);
      }
    }, 800);
    return () => clearInterval(interval);
  }, [gameStartedAt, code, navigate]);

  // si entramos tarde y la partida ya corre, directo al tablero
  useEffect(() => {
    if (game && (game.status === 'running' || game.status === 'paused') && !gameStartedAt) {
      navigate(`/game/${code}`);
    }
  }, [game, gameStartedAt, code, navigate]);

  if (!session) return null;

  // organizador = tiene la clave X-Admin-Token; puede además estar jugando
  const isOrganizer = !!adminToken;
  const visible = players.filter((p) => p.role !== 'ai_commentator');
  const online = visible.filter((p) => p.presence === 'online').length;
  const readyCount = visible.filter((p) => (p.role === 'player' || p.role === 'ai_player') && p.is_ready).length;

  function toggleReady() {
    audioService.unlock();
    const next = !ready;
    setReady(next);
    wsClient.send({ type: 'ready.set', payload: { ready: next } });
  }

  async function startGame() {
    audioService.unlock();
    if (!adminToken || !session) return;
    setStartError(null);
    try {
      await api.startGame(adminToken, session.gameId);
      // la navegación la dispara el evento game.started
    } catch (err) {
      setStartError(err instanceof Error ? err.message : 'No se pudo iniciar');
    }
  }

  return (
    <main className="mx-auto max-w-4xl p-6">
      <ConnectionBanner />

      {secondsLeft !== null && (
        <div data-testid="countdown" className="fixed inset-0 z-40 flex flex-col items-center justify-center bg-war-950/90 backdrop-blur">
          <p className="font-display text-2xl text-stone-300">La guerra empieza en</p>
          <p className="font-display text-9xl font-bold text-gold-400 animate-pulse">{secondsLeft}</p>
        </div>
      )}

      <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-bold text-gold-400">🏰 Sala de guerra</h1>
          <p className="text-sm text-stone-400" data-testid="lobby-game-name">{game?.name ?? '…'}</p>
        </div>
        <a href="discord://" className="rounded-lg border border-indigo-700 bg-indigo-950 px-3 py-1.5 text-sm text-indigo-300 hover:bg-indigo-900" title="Abrí Discord para la voz">
          🎧 Voz por Discord
        </a>
      </header>

      <div className="grid gap-6 md:grid-cols-[1fr_320px]">
        <section>
          <h2 className="mb-2 text-sm font-semibold tracking-wider text-stone-400">
            COMBATIENTES ({online}/{visible.length} conectados)
          </h2>
          <ul className="space-y-2" data-testid="lobby-players">
            {visible.map((p) => <PlayerCard key={p.id} player={p} isSelf={p.id === session.playerId} />)}
            {visible.length === 0 && <li className="text-sm text-stone-600">Esperando datos de la sala…</li>}
          </ul>

          <div className="mt-4 flex flex-col gap-2">
            {session.role !== 'spectator' && (
              <button onClick={toggleReady} data-testid="ready-button" className={`rounded-lg px-4 py-2.5 font-bold ${ready ? 'bg-green-700 text-green-100' : 'bg-gold-500 text-war-950 hover:bg-gold-400'}`}>
                {ready ? '✅ Listo (tocá para cancelar)' : '¿Listo para traicionar?'}
              </button>
            )}
            {isOrganizer && (
              <button onClick={startGame} data-testid="start-game" className="rounded-lg bg-red-700 px-4 py-2.5 font-bold text-red-50 hover:bg-red-600">
                ⚔️ Iniciar la guerra ({readyCount} listos)
              </button>
            )}
            {startError && <p role="alert" className="text-sm text-red-400">{startError}</p>}
          </div>
        </section>

        <aside>
          <h2 className="mb-2 text-sm font-semibold tracking-wider text-stone-400">CHARLA PREVIA</h2>
          <ChatPanel />
        </aside>
      </div>
    </main>
  );
}
