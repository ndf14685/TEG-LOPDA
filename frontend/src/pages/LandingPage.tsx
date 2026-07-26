import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, ApiRequestError } from '../services/api/apiClient';
import { audioService } from '../services/audio/AudioService';
import { useSessionStore } from '../state/sessionStore';
import { ALL_COLORS, PLAYER_COLOR_LABEL } from '../utils/playerColors';

export function LandingPage() {
  const navigate = useNavigate();
  const [server, setServer] = useState<'checking' | 'up' | 'down'>('checking');
  const [creating, setCreating] = useState(false);
  const [adminToken, setAdminToken] = useState(useSessionStore.getState().adminToken ?? '');
  const [gameName, setGameName] = useState('La Guerra de los Giles');
  const [nickname, setNickname] = useState('');
  const [color, setColor] = useState('red');
  const [gameMode, setGameMode] = useState('classic_50');
  const [joinUrl, setJoinUrl] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.health().then(() => setServer('up')).catch(() => setServer('down'));
  }, []);

  async function createGame(e: FormEvent) {
    e.preventDefault();
    audioService.unlock();
    setError(null);
    setCreating(true);
    try {
      const created = await api.createGame(adminToken, {
        name: gameName,
        config: { game_mode: gameMode },
      });
      // el organizador también juega: se auto-invita como PLAYER (el rol
      // admin del backend no se sienta a la mesa; organiza vía X-Admin-Token)
      const invite = await api.invitePlayer(adminToken, created.game.id, {
        nickname,
        role: 'player',
        color,
      });
      if (!invite.token) throw new Error('el servidor no devolvió token para el admin');
      const joined = await api.joinConfirm(created.game.code, invite.token);
      useSessionStore.getState().setAdminToken(adminToken);
      useSessionStore.getState().setSession({
        code: created.game.code,
        gameId: created.game.id,
        token: invite.token,
        playerId: joined.player.id,
        nickname: joined.player.nickname,
        role: joined.player.role,
      });
      navigate(`/admin/${created.game.id}`);
    } catch (err) {
      if (err instanceof ApiRequestError && err.status === 401) {
        setError('Esa no es la clave de organizador. Si sos jugador, no necesitás clave: pedile el link de invitación al que arma la partida y pegalo abajo en «¿Te invitaron?».');
      } else {
        setError(err instanceof Error ? err.message : 'No se pudo crear la partida');
      }
    } finally {
      setCreating(false);
    }
  }

  function joinByLink(e: FormEvent) {
    e.preventDefault();
    try {
      const url = new URL(joinUrl, location.origin);
      if (!url.pathname.startsWith('/join/')) throw new Error();
      navigate(url.pathname);
    } catch {
      setError('Ese link no parece un link de invitación válido.');
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center gap-8 p-6">
      <header className="text-center">
        <h1 className="font-display text-5xl font-bold tracking-wide text-gold-400 drop-shadow-lg">⚔️ TEG LOPDA</h1>
        <p className="mt-2 text-lg text-stone-400 italic">«La Odisea de Perder Después de Aliarte»</p>
        <p className="mt-1 text-sm" data-testid="server-status">
          {server === 'checking' && '🟡 verificando cuartel general…'}
          {server === 'up' && <span className="text-green-500">🟢 servidor operativo</span>}
          {server === 'down' && <span className="text-red-500">🔴 servidor caído — culpa de alguien, seguro</span>}
        </p>
      </header>

      <section className="w-full rounded-xl border border-war-700 bg-war-900 p-6">
        <h2 className="mb-4 font-display text-xl font-bold text-stone-100">Fundar una guerra <span className="text-xs font-normal text-stone-500">(solo el organizador)</span></h2>
        <form onSubmit={createGame} className="grid gap-3 sm:grid-cols-2">
          <label className="sm:col-span-2 text-sm">
            <span className="mb-1 block text-stone-400">Clave de organizador</span>
            <input type="password" value={adminToken} onChange={(e) => setAdminToken(e.target.value)} required autoComplete="off" data-testid="admin-token" className="w-full rounded border border-war-700 bg-war-800 px-3 py-2 outline-none focus:border-gold-500" />
          </label>
          <label className="sm:col-span-2 text-sm">
            <span className="mb-1 block text-stone-400">Nombre de la partida</span>
            <input value={gameName} onChange={(e) => setGameName(e.target.value)} required maxLength={60} className="w-full rounded border border-war-700 bg-war-800 px-3 py-2 outline-none focus:border-gold-500" />
          </label>
          <label className="sm:col-span-2 text-sm">
            <span className="mb-1 block text-stone-400">Mapa</span>
            <select value={gameMode} onChange={(e) => setGameMode(e.target.value)} data-testid="game-mode" className="w-full rounded border border-war-700 bg-war-800 px-3 py-2 outline-none focus:border-gold-500">
              <option value="classic_26">Táctico — 26 países (2 a 8 jugadores)</option>
              <option value="classic_50">Mundo — 50 países (2 a 10 jugadores)</option>
              <option value="mega_world_100">Mega Mundo — 100 territorios (hasta 20 jugadores)</option>
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-stone-400">Tu apodo de guerra</span>
            <input value={nickname} onChange={(e) => setNickname(e.target.value)} required maxLength={64} data-testid="admin-nickname" className="w-full rounded border border-war-700 bg-war-800 px-3 py-2 outline-none focus:border-gold-500" />
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-stone-400">Color</span>
            <select value={color} onChange={(e) => setColor(e.target.value)} className="w-full rounded border border-war-700 bg-war-800 px-3 py-2">
              {ALL_COLORS.map((c) => <option key={c} value={c}>{PLAYER_COLOR_LABEL[c]}</option>)}
            </select>
          </label>
          <button disabled={creating || server !== 'up'} data-testid="create-game" className="sm:col-span-2 rounded-lg bg-gold-500 px-4 py-2.5 font-bold text-war-950 hover:bg-gold-400 disabled:opacity-40">
            {creating ? 'Fundando…' : '⚔️ Crear partida'}
          </button>
        </form>
      </section>

      <section className="w-full rounded-xl border border-war-700 bg-war-900 p-6">
        <h2 className="mb-1 font-display text-xl font-bold text-stone-100">¿Te invitaron?</h2>
        <p className="mb-3 text-sm text-stone-400">Si vas a jugar, esto es todo lo que necesitás: pedile el link al organizador y pegalo acá. La clave de arriba es solo para quien funda la partida.</p>
        <form onSubmit={joinByLink} className="flex gap-2">
          <input value={joinUrl} onChange={(e) => setJoinUrl(e.target.value)} placeholder="Pegá tu link de invitación" aria-label="Link de invitación" className="min-w-0 flex-1 rounded border border-war-700 bg-war-800 px-3 py-2 text-sm outline-none focus:border-gold-500" />
          <button className="rounded border border-war-700 bg-war-800 px-4 py-2 text-sm font-semibold hover:border-gold-500">Entrar</button>
        </form>
      </section>

      {error && <p role="alert" className="text-sm text-red-400">{error}</p>}
      <footer className="text-xs text-stone-600">Se juega con voz en Discord 🎧 — acá se juega, allá se grita.</footer>
    </main>
  );
}
