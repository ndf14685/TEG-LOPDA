import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api/apiClient';
import { audioService } from '../services/audio/AudioService';
import { useSessionStore } from '../state/sessionStore';
import { ALL_COLORS, PLAYER_COLOR_LABEL } from '../utils/playerColors';
import type { PlayerColor } from '@teg/contracts';

const AVATARS = ['avatar.general.001', 'avatar.zorro.001', 'avatar.pulpo.001', 'avatar.calavera.001', 'avatar.corona.001', 'avatar.alien.001'];

export function LandingPage() {
  const navigate = useNavigate();
  const [server, setServer] = useState<'checking' | 'up' | 'down'>('checking');
  const [creating, setCreating] = useState(false);
  const [gameName, setGameName] = useState('La Guerra de los Giles');
  const [name, setName] = useState('');
  const [nickname, setNickname] = useState('');
  const [color, setColor] = useState<PlayerColor>('red');
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
      const res = await api.createGame({
        gameName,
        admin: { name: name || nickname, nickname: nickname || name, color, avatarId: 'avatar.corona.001' },
      });
      // el admin canjea su propio token como cualquier jugador
      const session = await api.createSession(res.adminToken);
      useSessionStore.getState().setSession(session);
      useSessionStore.getState().setAdminToken(res.adminToken);
      sessionStorage.setItem(`teg.admin.${res.gameId}`, res.adminToken);
      navigate(`/admin/${res.gameId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo crear la partida');
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
        <h2 className="mb-4 font-display text-xl font-bold text-stone-100">Fundar una guerra</h2>
        <form onSubmit={createGame} className="grid gap-3 sm:grid-cols-2">
          <label className="sm:col-span-2 text-sm">
            <span className="mb-1 block text-stone-400">Nombre de la partida</span>
            <input value={gameName} onChange={(e) => setGameName(e.target.value)} required maxLength={60} className="w-full rounded border border-war-700 bg-war-800 px-3 py-2 outline-none focus:border-gold-500" />
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-stone-400">Tu nombre</span>
            <input value={name} onChange={(e) => setName(e.target.value)} required maxLength={60} data-testid="admin-name" className="w-full rounded border border-war-700 bg-war-800 px-3 py-2 outline-none focus:border-gold-500" />
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-stone-400">Tu apodo de guerra</span>
            <input value={nickname} onChange={(e) => setNickname(e.target.value)} required maxLength={40} data-testid="admin-nickname" className="w-full rounded border border-war-700 bg-war-800 px-3 py-2 outline-none focus:border-gold-500" />
          </label>
          <label className="text-sm sm:col-span-2">
            <span className="mb-1 block text-stone-400">Color</span>
            <select value={color} onChange={(e) => setColor(e.target.value as PlayerColor)} className="w-full rounded border border-war-700 bg-war-800 px-3 py-2">
              {ALL_COLORS.map((c) => <option key={c} value={c}>{PLAYER_COLOR_LABEL[c]}</option>)}
            </select>
          </label>
          <button disabled={creating || server !== 'up'} data-testid="create-game" className="sm:col-span-2 rounded-lg bg-gold-500 px-4 py-2.5 font-bold text-war-950 hover:bg-gold-400 disabled:opacity-40">
            {creating ? 'Fundando…' : '⚔️ Crear partida'}
          </button>
        </form>
      </section>

      <section className="w-full rounded-xl border border-war-700 bg-war-900 p-6">
        <h2 className="mb-3 font-display text-xl font-bold text-stone-100">¿Te invitaron?</h2>
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
export { AVATARS };
