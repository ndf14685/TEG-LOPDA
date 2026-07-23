import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { wsClient } from '../services/websocket/wsClient';
import { bindWsToStores } from '../services/websocket/bindStores';
import { useSessionStore } from '../state/sessionStore';
import { useGameStore } from '../state/gameStore';
import { PlayerCard } from '../components/players/PlayerCard';
import { ChatPanel } from '../components/chat/ChatPanel';
import { ConnectionBanner } from '../components/ConnectionBanner';
import { audioService } from '../services/audio/AudioService';

export function LobbyPage() {
  const { gameId = '' } = useParams();
  const navigate = useNavigate();
  const session = useSessionStore((s) => s.session);
  const restore = useSessionStore((s) => s.restore);
  const lobby = useGameStore((s) => s.lobby);
  const snapshot = useGameStore((s) => s.snapshot);
  const countdownMs = useGameStore((s) => s.countdownMs);
  const [ready, setReady] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState<number | null>(null);

  // sesión: en memoria o restaurada de sessionStorage
  useEffect(() => {
    if (!session && !restore(gameId)) navigate('/');
  }, [session, gameId, restore, navigate]);

  useEffect(() => {
    if (!session) return;
    bindWsToStores();
    wsClient.connect(session.sessionId);
  }, [session]);

  // cuenta regresiva de inicio
  useEffect(() => {
    if (countdownMs === null) {
      setSecondsLeft(null);
      return;
    }
    audioService.unlock();
    let remaining = Math.ceil(countdownMs / 1000);
    setSecondsLeft(remaining);
    const interval = setInterval(() => {
      remaining -= 1;
      setSecondsLeft(remaining);
      if (remaining <= 0) clearInterval(interval);
    }, 1000);
    return () => clearInterval(interval);
  }, [countdownMs]);

  // cuando llega el snapshot inicial, a la batalla
  useEffect(() => {
    if (snapshot && snapshot.status === 'in-game') navigate(`/game/${gameId}`);
  }, [snapshot, gameId, navigate]);

  if (!session) return null;

  const isAdmin = session.role === 'admin';
  const players = lobby?.players ?? [];
  const nonAdminReady = players.filter((p) => p.role === 'player' && p.ready).length;

  function toggleReady() {
    audioService.unlock();
    const next = !ready;
    setReady(next);
    wsClient.send({ type: 'player.ready', ready: next });
  }

  function startGame() {
    audioService.unlock();
    wsClient.send({ type: 'game.start' });
  }

  return (
    <main className="mx-auto max-w-4xl p-6">
      <ConnectionBanner />

      {secondsLeft !== null && secondsLeft > 0 && (
        <div data-testid="countdown" className="fixed inset-0 z-40 flex flex-col items-center justify-center bg-war-950/90 backdrop-blur">
          <p className="font-display text-2xl text-stone-300">La guerra empieza en</p>
          <p className="font-display text-9xl font-bold text-gold-400 animate-pulse">{secondsLeft}</p>
        </div>
      )}

      <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-bold text-gold-400">🏰 Sala de guerra</h1>
          <p className="text-sm text-stone-400" data-testid="lobby-game-name">{lobby?.gameName ?? '…'}</p>
        </div>
        <a href="discord://" className="rounded-lg border border-indigo-700 bg-indigo-950 px-3 py-1.5 text-sm text-indigo-300 hover:bg-indigo-900" title="Abrí Discord para la voz">
          🎧 Voz por Discord
        </a>
      </header>

      <div className="grid gap-6 md:grid-cols-[1fr_320px]">
        <section>
          <h2 className="mb-2 text-sm font-semibold tracking-wider text-stone-400">
            COMBATIENTES ({players.filter((p) => p.connection === 'connected').length}/{players.length} conectados)
          </h2>
          <ul className="space-y-2" data-testid="lobby-players">
            {players.map((p) => <PlayerCard key={p.id} player={p} isSelf={p.id === session.playerId} />)}
            {players.length === 0 && <li className="text-sm text-stone-600">Esperando datos de la sala…</li>}
          </ul>

          <div className="mt-4 flex gap-2">
            {!isAdmin && (
              <button onClick={toggleReady} data-testid="ready-button" className={`flex-1 rounded-lg px-4 py-2.5 font-bold ${ready ? 'bg-green-700 text-green-100' : 'bg-gold-500 text-war-950 hover:bg-gold-400'}`}>
                {ready ? '✅ Listo (tocá para cancelar)' : '¿Listo para traicionar?'}
              </button>
            )}
            {isAdmin && (
              <button onClick={startGame} data-testid="start-game" className="flex-1 rounded-lg bg-red-700 px-4 py-2.5 font-bold text-red-50 hover:bg-red-600">
                ⚔️ Iniciar la guerra ({nonAdminReady} listos)
              </button>
            )}
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
