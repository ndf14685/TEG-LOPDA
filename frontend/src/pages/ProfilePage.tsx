import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import type { Profile } from '@teg/contracts';
import { api } from '../services/api/apiClient';
import { colorValue } from '../utils/playerColors';
import { PlayerAvatar } from '../components/players/PlayerAvatar';
import { TauntStudio } from '../components/taunts/TauntStudio';

const PROFILE_TOKEN_KEY = 'teg.profileToken';

export function getStoredProfileToken(): string | null {
  return localStorage.getItem(PROFILE_TOKEN_KEY);
}

/** Link personal permanente: /p/{token}. Asocia este navegador al perfil. */
export function ProfilePage() {
  const { token = '' } = useParams();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [studioOpen, setStudioOpen] = useState(false);
  const [history, setHistory] = useState<{
    games_played: number;
    totals: Record<string, number>;
    trophies: Record<string, number>;
  } | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .resolveProfile(token)
      .then((res) => {
        if (cancelled) return;
        localStorage.setItem(PROFILE_TOKEN_KEY, token);
        setProfile(res.profile);
        void fetch(`/api/profile/${encodeURIComponent(token)}/stats`)
          .then((r) => (r.ok ? r.json() : null))
          .then((r) => { if (!cancelled && r) setHistory(r.stats); });
      })
      .catch(() => {
        if (!cancelled) setError('Este link de perfil no es válido o fue regenerado.');
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center p-8">
        <p role="alert" className="text-red-400">{error}</p>
      </main>
    );
  }
  if (!profile) {
    return <main className="p-8 text-stone-400">Cargando tu perfil…</main>;
  }

  return (
    <main className="mx-auto max-w-2xl p-6">
      <header className="mb-6 text-center">
        <div className="inline-block">
          <PlayerAvatar avatarAssetId={profile.avatar_asset_id} color={profile.color} role="player" size="lg" />
        </div>
        <h1 className="mt-2 font-display text-3xl font-bold" style={{ color: colorValue(profile.color) }}>
          {profile.nickname}
        </h1>
        <p className="text-sm text-stone-400">
          Este navegador quedó asociado a tu perfil. Guardá este link: es tu identidad para todas las partidas.
        </p>
      </header>

      <section className="rounded-xl border border-war-700 bg-war-900 p-5 text-center" data-testid="profile-card">
        <p className="text-sm text-stone-300">
          Cuando el organizador te invite a una partida, tus audios y estadísticas quedan ligados a este perfil.
        </p>
        <button
          onClick={() => setStudioOpen(true)}
          data-testid="open-taunt-studio"
          className="mt-4 rounded-xl bg-gold-500 px-5 py-2.5 text-sm font-bold text-war-950 hover:bg-gold-400"
        >
          🎙️ Grabar mis audios de guerra
        </button>
      </section>

      <section className="mt-4 rounded-xl border border-war-700 bg-war-900 p-5" data-testid="profile-history">
        <h2 className="mb-3 text-center text-xs font-semibold tracking-wider text-stone-400">
          📊 TU HISTORIAL DE GUERRA
        </h2>
        {!history || history.games_played === 0 ? (
          <p className="text-center text-sm text-stone-500">
            Todavía no jugaste ninguna partida con este perfil. Tus números aparecen acá al terminar la primera.
          </p>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-2 text-center sm:grid-cols-4">
              {[
                ['Partidas', history.games_played],
                ['Conquistas', history.totals.conquests ?? 0],
                ['Ataques', history.totals.attacks_launched ?? 0],
                ['Eliminaciones', history.totals.eliminations ?? 0],
                ['Seises', history.totals.dice_six ?? 0],
                ['Unos', history.totals.dice_one ?? 0],
                ['Traiciones', history.totals.betrayals ?? 0],
                ['Países perdidos', history.totals.territories_lost ?? 0],
              ].map(([label, value]) => (
                <div key={String(label)} className="rounded-lg border border-war-700 bg-war-950/60 p-2">
                  <p className="text-lg font-black text-gold-400">{value}</p>
                  <p className="text-[10px] text-stone-400">{label}</p>
                </div>
              ))}
            </div>
            {Object.keys(history.trophies).length > 0 && (
              <div className="mt-3">
                <p className="mb-1 text-center text-[10px] font-semibold text-stone-500">VITRINA DE TROFEOS</p>
                <div className="flex flex-wrap justify-center gap-1.5">
                  {Object.entries(history.trophies).map(([title, count]) => (
                    <span key={title} className="rounded-full border border-gold-500/40 bg-gold-950/30 px-2 py-0.5 text-[11px] text-gold-300">
                      {title} ×{count}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </section>

      {studioOpen && <TauntStudio profileToken={token} onClose={() => setStudioOpen(false)} />}
    </main>
  );
}
