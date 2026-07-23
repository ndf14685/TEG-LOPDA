import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import type { AdminGameView, PlayerColor, PlayerRole } from '@teg/contracts';
import { api } from '../services/api/apiClient';
import { useSessionStore } from '../state/sessionStore';
import { ALL_COLORS, PLAYER_COLOR_LABEL, PLAYER_COLOR_VAR } from '../utils/playerColors';
import { assetRegistry } from '../services/assets/AssetRegistry';
import { AVATARS } from './LandingPage';

export function AdminPage() {
  const { gameId = '' } = useParams();
  const navigate = useNavigate();
  const [view, setView] = useState<AdminGameView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const [name, setName] = useState('');
  const [nickname, setNickname] = useState('');
  const [color, setColor] = useState<PlayerColor>('blue');
  const [avatarId, setAvatarId] = useState(AVATARS[1]);
  const [role, setRole] = useState<PlayerRole>('player');

  const adminToken = useSessionStore((s) => s.adminToken) ?? sessionStorage.getItem(`teg.admin.${gameId}`);

  const refresh = useCallback(async () => {
    if (!adminToken) return;
    try {
      setView(await api.adminView(gameId, adminToken));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando la partida');
    }
  }, [gameId, adminToken]);

  useEffect(() => {
    if (!adminToken) {
      navigate('/');
      return;
    }
    void refresh();
  }, [adminToken, navigate, refresh]);

  async function createPlayer(e: FormEvent) {
    e.preventDefault();
    if (!adminToken) return;
    setError(null);
    try {
      await api.createPlayer(gameId, adminToken, {
        profile: { name, nickname, color, avatarId, tauntAudioIds: [], trustLevel: 5, titles: [], relationships: {} },
        role,
      });
      setName('');
      setNickname('');
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo crear el jugador');
    }
  }

  async function copyLink(playerId: string, joinPath: string) {
    await navigator.clipboard.writeText(location.origin + joinPath).catch(() => {});
    setCopiedId(playerId);
    setTimeout(() => setCopiedId(null), 1500);
  }

  async function revoke(playerId: string) {
    if (!adminToken) return;
    await api.revokeLink(gameId, adminToken, playerId);
    await refresh();
  }

  async function regenerate(playerId: string) {
    if (!adminToken) return;
    await api.regenerateLink(gameId, adminToken, playerId);
    await refresh();
  }

  if (!view) {
    return <main className="p-8 text-stone-400">{error ?? 'Cargando cuartel general…'}</main>;
  }

  return (
    <main className="mx-auto max-w-4xl p-6">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-bold text-gold-400">🎖️ Cuartel general</h1>
          <p className="text-sm text-stone-400">{view.gameName} · <code className="text-xs">{view.gameId}</code></p>
        </div>
        <Link to={`/lobby/${gameId}`} data-testid="go-lobby" className="rounded-lg bg-gold-500 px-4 py-2 font-bold text-war-950 hover:bg-gold-400">
          Ir al lobby →
        </Link>
      </header>

      {error && <p role="alert" className="mb-4 text-sm text-red-400">{error}</p>}

      <section className="mb-6 rounded-xl border border-war-700 bg-war-900 p-5">
        <h2 className="mb-3 font-display text-lg font-bold">Reclutar jugador</h2>
        <form onSubmit={createPlayer} className="grid gap-3 sm:grid-cols-2">
          <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Nombre" maxLength={60} data-testid="new-player-name" className="rounded border border-war-700 bg-war-800 px-3 py-2 text-sm outline-none focus:border-gold-500" />
          <input value={nickname} onChange={(e) => setNickname(e.target.value)} required placeholder="Apodo de guerra" maxLength={40} data-testid="new-player-nickname" className="rounded border border-war-700 bg-war-800 px-3 py-2 text-sm outline-none focus:border-gold-500" />
          <select value={color} onChange={(e) => setColor(e.target.value as PlayerColor)} aria-label="Color" className="rounded border border-war-700 bg-war-800 px-3 py-2 text-sm">
            {ALL_COLORS.map((c) => <option key={c} value={c}>{PLAYER_COLOR_LABEL[c]}</option>)}
          </select>
          <div className="flex items-center gap-1" role="radiogroup" aria-label="Avatar">
            {AVATARS.map((id) => (
              <button
                key={id}
                type="button"
                role="radio"
                aria-checked={avatarId === id}
                onClick={() => setAvatarId(id)}
                className={`rounded-full p-1.5 text-xl ${avatarId === id ? 'bg-war-700 ring-2 ring-gold-500' : 'hover:bg-war-800'}`}
              >
                {assetRegistry.emoji(id)}
              </button>
            ))}
          </div>
          <select value={role} onChange={(e) => setRole(e.target.value as PlayerRole)} aria-label="Rol" className="rounded border border-war-700 bg-war-800 px-3 py-2 text-sm">
            <option value="player">Jugador</option>
            <option value="spectator">Espectador</option>
            <option value="ai-player">Jugador IA</option>
          </select>
          <button data-testid="create-player" className="rounded-lg bg-gold-500 px-4 py-2 font-bold text-war-950 hover:bg-gold-400">+ Generar link</button>
        </form>
      </section>

      <section className="rounded-xl border border-war-700 bg-war-900 p-5">
        <h2 className="mb-3 font-display text-lg font-bold">Links de invitación</h2>
        <ul className="space-y-2">
          {view.links.map((link) => (
            <li key={link.playerId} data-testid={`link-row-${link.profile.nickname}`} className="flex flex-wrap items-center gap-2 rounded-lg border border-war-700 bg-war-800/60 px-3 py-2">
              <span className="text-xl">{assetRegistry.emoji(link.profile.avatarId)}</span>
              <span className="font-semibold" style={{ color: PLAYER_COLOR_VAR[link.profile.color] }}>{link.profile.nickname}</span>
              <span className="text-xs text-stone-500">({link.profile.name} · {link.role})</span>
              {link.revoked && <span className="rounded bg-red-900/70 px-1.5 py-0.5 text-[10px] text-red-200">REVOCADO</span>}
              <span className="ml-auto flex gap-1.5">
                {!link.revoked && (
                  <button onClick={() => copyLink(link.playerId, link.joinPath)} data-testid={`copy-link-${link.profile.nickname}`} className="rounded border border-war-700 px-2 py-1 text-xs hover:border-gold-500">
                    {copiedId === link.playerId ? '✅ copiado' : '📋 copiar link'}
                  </button>
                )}
                {!link.revoked && link.role !== 'admin' && (
                  <button onClick={() => revoke(link.playerId)} className="rounded border border-war-700 px-2 py-1 text-xs hover:border-red-500">🚫 revocar</button>
                )}
                {link.role !== 'admin' && (
                  <button onClick={() => regenerate(link.playerId)} className="rounded border border-war-700 px-2 py-1 text-xs hover:border-gold-500">♻️ regenerar</button>
                )}
              </span>
              {/* el token no se muestra completo: sólo vive dentro del botón copiar */}
            </li>
          ))}
        </ul>
        <p className="mt-3 text-xs text-stone-500">Pasale a cada uno su link por privado. El link identifica al jugador: no lo publiques en el grupo.</p>
      </section>
    </main>
  );
}
