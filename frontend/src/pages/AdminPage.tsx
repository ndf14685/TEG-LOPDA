import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import type { AdminGameDetailResponse, PlayerRole, Profile } from '@teg/contracts';
import { api, toFrontendUrl } from '../services/api/apiClient';
import { useSessionStore } from '../state/sessionStore';
import { ALL_COLORS, PLAYER_COLOR_LABEL, colorValue } from '../utils/playerColors';
import { PlayerAvatar } from '../components/players/PlayerAvatar';

/**
 * Los tokens en claro solo existen en la respuesta de invite/regenerate.
 * El admin los retiene en su navegador (sessionStorage) para poder copiar
 * los links; el server solo guarda hashes.
 */
function linksKey(gameId: string) {
  return `teg.links.${gameId}`;
}
function loadLinks(gameId: string): Record<string, string> {
  try {
    return JSON.parse(sessionStorage.getItem(linksKey(gameId)) ?? '{}');
  } catch {
    return {};
  }
}
function saveLink(gameId: string, playerId: string, joinUrl: string) {
  const links = loadLinks(gameId);
  links[playerId] = joinUrl;
  sessionStorage.setItem(linksKey(gameId), JSON.stringify(links));
}

/** Links personales de perfil: persisten en este navegador (localStorage). */
const PROFILE_LINKS_KEY = 'teg.profile.links';
function loadProfileLinks(): Record<string, string> {
  try {
    return JSON.parse(localStorage.getItem(PROFILE_LINKS_KEY) ?? '{}');
  } catch {
    return {};
  }
}
function saveProfileLink(profileId: string, url: string) {
  const links = loadProfileLinks();
  links[profileId] = url;
  localStorage.setItem(PROFILE_LINKS_KEY, JSON.stringify(links));
}

export function AdminPage() {
  const { gameId = '' } = useParams();
  const navigate = useNavigate();
  const adminToken = useSessionStore((s) => s.adminToken);
  const selfPlayerId = useSessionStore((s) => s.session?.playerId);
  const [detail, setDetail] = useState<AdminGameDetailResponse | null>(null);
  const [links, setLinks] = useState<Record<string, string>>(() => loadLinks(gameId));
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const [nickname, setNickname] = useState('');
  const [color, setColor] = useState('blue');
  const [role, setRole] = useState<PlayerRole>('player');

  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [profileLinks, setProfileLinks] = useState<Record<string, string>>(() => loadProfileLinks());
  const [newProfileNickname, setNewProfileNickname] = useState('');
  const [newProfileColor, setNewProfileColor] = useState('blue');

  const refresh = useCallback(async () => {
    if (!adminToken) return;
    try {
      setDetail(await api.gameDetail(adminToken, gameId));
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
    void api.listProfiles(adminToken).then((r) => setProfiles(r.profiles)).catch(() => {});
  }, [adminToken, navigate, refresh]);

  async function createProfile(e: FormEvent) {
    e.preventDefault();
    if (!adminToken) return;
    setError(null);
    try {
      const res = await api.createProfile(adminToken, {
        nickname: newProfileNickname,
        color: newProfileColor,
      });
      saveProfileLink(res.profile.id, res.profile_url);
      setProfileLinks(loadProfileLinks());
      setProfiles((prev) => [...prev, res.profile]);
      setNewProfileNickname('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo crear el perfil');
    }
  }

  async function copyProfileLink(profileId: string) {
    let url = profileLinks[profileId];
    if (!url && adminToken) {
      // el token no está en este navegador: regenerar emite uno nuevo
      const res = await api.regenerateProfileToken(adminToken, profileId);
      saveProfileLink(profileId, res.profile_url);
      setProfileLinks(loadProfileLinks());
      url = res.profile_url;
    }
    if (!url) return;
    await navigator.clipboard.writeText(toFrontendUrl(url)).catch(() => {});
    setCopiedId(`profile-${profileId}`);
    setTimeout(() => setCopiedId(null), 1500);
  }

  async function inviteProfile(profileId: string) {
    if (!adminToken) return;
    setError(null);
    try {
      const res = await api.invitePlayer(adminToken, gameId, { profile_id: profileId, role: 'player' });
      if (res.join_url) {
        saveLink(gameId, res.player.id, res.join_url);
        setLinks(loadLinks(gameId));
      }
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo invitar al perfil');
    }
  }

  async function invite(e: FormEvent) {
    e.preventDefault();
    if (!adminToken) return;
    setError(null);
    try {
      const res = await api.invitePlayer(adminToken, gameId, { nickname, role, color });
      if (res.join_url) {
        saveLink(gameId, res.player.id, res.join_url);
        setLinks(loadLinks(gameId));
      }
      setNickname('');
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo invitar al jugador');
    }
  }

  async function copyLink(playerId: string) {
    const url = links[playerId];
    if (!url) return;
    await navigator.clipboard.writeText(toFrontendUrl(url)).catch(() => {});
    setCopiedId(playerId);
    setTimeout(() => setCopiedId(null), 1500);
  }

  async function regenerate(playerId: string) {
    if (!adminToken) return;
    const res = await api.regenerateToken(adminToken, gameId, playerId);
    saveLink(gameId, playerId, res.join_url);
    setLinks(loadLinks(gameId));
    await refresh();
  }

  async function kick(playerId: string) {
    if (!adminToken) return;
    await api.kickPlayer(adminToken, gameId, playerId);
    await refresh();
  }

  if (!detail) {
    return <main className="p-8 text-stone-400">{error ?? 'Cargando cuartel general…'}</main>;
  }

  const code = detail.game.code;

  return (
    <main className="mx-auto max-w-4xl p-6">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-bold text-gold-400">🎖️ Cuartel general</h1>
          <p className="text-sm text-stone-400">
            {detail.game.name} · sala <code className="text-xs">{code}</code> · estado {detail.game.status}
          </p>
        </div>
        <Link to={`/lobby/${code}`} data-testid="go-lobby" className="rounded-lg bg-gold-500 px-4 py-2 font-bold text-war-950 hover:bg-gold-400">
          Ir al lobby →
        </Link>
      </header>

      {error && <p role="alert" className="mb-4 text-sm text-red-400">{error}</p>}

      <section className="mb-6 rounded-xl border border-war-700 bg-war-900 p-5" data-testid="profiles-panel">
        <h2 className="mb-3 font-display text-lg font-bold">👥 El grupo (perfiles permanentes)</h2>
        <p className="mb-3 text-xs text-stone-500">
          Cada amigo tiene su perfil y su link personal para siempre: audios y estadísticas quedan ligados a él.
          Invitalo a esta partida con un click.
        </p>
        <form onSubmit={createProfile} className="mb-3 grid gap-3 sm:grid-cols-4">
          <input
            value={newProfileNickname}
            onChange={(e) => setNewProfileNickname(e.target.value)}
            required
            placeholder="Nombre del amigo"
            maxLength={64}
            data-testid="new-profile-nickname"
            className="rounded border border-war-700 bg-war-800 px-3 py-2 text-sm outline-none focus:border-gold-500 sm:col-span-2"
          />
          <select
            value={newProfileColor}
            onChange={(e) => setNewProfileColor(e.target.value)}
            aria-label="Color favorito"
            className="rounded border border-war-700 bg-war-800 px-3 py-2 text-sm"
          >
            {ALL_COLORS.map((c) => <option key={c} value={c}>{PLAYER_COLOR_LABEL[c]}</option>)}
          </select>
          <button data-testid="create-profile" className="rounded-lg border border-gold-500/50 px-4 py-2 text-sm font-bold text-gold-400 hover:bg-war-800">
            + Crear perfil
          </button>
        </form>
        {profiles.length > 0 && (
          <ul className="space-y-1.5">
            {profiles.map((p) => (
              <li key={p.id} className="flex flex-wrap items-center gap-2 rounded-lg border border-war-700 bg-war-800/60 px-3 py-1.5">
                <span className="font-semibold text-sm" style={{ color: colorValue(p.color) }}>{p.nickname}</span>
                <span className="ml-auto flex gap-1.5">
                  <button onClick={() => copyProfileLink(p.id)} className="rounded border border-war-700 px-2 py-1 text-xs hover:border-gold-500">
                    {copiedId === `profile-${p.id}` ? '✅ copiado' : '🔗 link personal'}
                  </button>
                  {detail.game.status === 'lobby' || detail.game.status === 'ready' ? (
                    <button
                      onClick={() => inviteProfile(p.id)}
                      data-testid={`invite-profile-${p.nickname}`}
                      disabled={detail.players.some((pl) => pl.profile_id === p.id && !pl.token_revoked)}
                      className="rounded bg-gold-500 px-2 py-1 text-xs font-bold text-war-950 hover:bg-gold-400 disabled:opacity-30"
                    >
                      ⚔️ invitar a esta partida
                    </button>
                  ) : null}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="mb-6 rounded-xl border border-war-700 bg-war-900 p-5">
        <h2 className="mb-3 font-display text-lg font-bold">Reclutar jugador</h2>
        <form onSubmit={invite} className="grid gap-3 sm:grid-cols-4">
          <input value={nickname} onChange={(e) => setNickname(e.target.value)} required placeholder="Apodo de guerra" maxLength={64} data-testid="new-player-nickname" className="rounded border border-war-700 bg-war-800 px-3 py-2 text-sm outline-none focus:border-gold-500 sm:col-span-2" />
          <select value={color} onChange={(e) => setColor(e.target.value)} aria-label="Color" className="rounded border border-war-700 bg-war-800 px-3 py-2 text-sm">
            {ALL_COLORS.map((c) => <option key={c} value={c}>{PLAYER_COLOR_LABEL[c]}</option>)}
          </select>
          <select value={role} onChange={(e) => setRole(e.target.value as PlayerRole)} aria-label="Rol" className="rounded border border-war-700 bg-war-800 px-3 py-2 text-sm">
            <option value="player">Jugador</option>
            <option value="spectator">Espectador</option>
            <option value="ai_player">Jugador IA</option>
          </select>
          <button data-testid="create-player" className="rounded-lg bg-gold-500 px-4 py-2 font-bold text-war-950 hover:bg-gold-400 sm:col-span-4">+ Generar link</button>
        </form>
      </section>

      <section className="rounded-xl border border-war-700 bg-war-900 p-5">
        <h2 className="mb-3 font-display text-lg font-bold">Tropa e invitaciones</h2>
        <ul className="space-y-2">
          {detail.players.map((p) => (
            <li key={p.id} data-testid={`link-row-${p.nickname}`} className="flex flex-wrap items-center gap-2 rounded-lg border border-war-700 bg-war-800/60 px-3 py-2">
              <PlayerAvatar avatarAssetId={p.avatar_asset_id} role={p.role} color={p.color} size="sm" />
              <span className="font-semibold" style={{ color: colorValue(p.color) }}>{p.nickname}</span>
              <span className="text-xs text-stone-500">({p.role} · {p.presence ?? '—'})</span>
              {p.token_revoked && <span className="rounded bg-red-900/70 px-1.5 py-0.5 text-[10px] text-red-200">REVOCADO</span>}
              {p.is_ready && <span className="text-xs">✅</span>}
              <span className="ml-auto flex gap-1.5">
                {links[p.id] && !p.token_revoked && (
                  <button onClick={() => copyLink(p.id)} data-testid={`copy-link-${p.nickname}`} className="rounded border border-war-700 px-2 py-1 text-xs hover:border-gold-500">
                    {copiedId === p.id ? '✅ copiado' : '📋 copiar link'}
                  </button>
                )}
                {p.role !== 'admin' && p.role !== 'ai_player' && p.id !== selfPlayerId && (
                  <>
                    <button onClick={() => regenerate(p.id)} className="rounded border border-war-700 px-2 py-1 text-xs hover:border-gold-500">♻️ regenerar</button>
                    {detail.game.status === 'running' && (
                      <button
                        onClick={async () => { if (adminToken) { await api.convertToAi(adminToken, gameId, p.id); await refresh(); } }}
                        title="El bot juega por él hasta que vuelva a entrar con su link"
                        className="rounded border border-war-700 px-2 py-1 text-xs hover:border-sky-500"
                      >
                        🤖 que siga la IA
                      </button>
                    )}
                    <button onClick={() => kick(p.id)} className="rounded border border-war-700 px-2 py-1 text-xs hover:border-red-500">🚫 expulsar</button>
                  </>
                )}
              </span>
            </li>
          ))}
        </ul>
        <p className="mt-3 text-xs text-stone-500">
          El link identifica al jugador: pasáselo por privado. El token solo se muestra al crearlo o regenerarlo — este navegador lo recuerda para copiar; el servidor no.
        </p>
      </section>
    </main>
  );
}
