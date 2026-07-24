import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import type { Profile } from '@teg/contracts';
import { api } from '../services/api/apiClient';
import { colorValue } from '../utils/playerColors';
import { PlayerAvatar } from '../components/players/PlayerAvatar';

const PROFILE_TOKEN_KEY = 'teg.profileToken';

export function getStoredProfileToken(): string | null {
  return localStorage.getItem(PROFILE_TOKEN_KEY);
}

/** Link personal permanente: /p/{token}. Asocia este navegador al perfil. */
export function ProfilePage() {
  const { token = '' } = useParams();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .resolveProfile(token)
      .then((res) => {
        if (cancelled) return;
        localStorage.setItem(PROFILE_TOKEN_KEY, token);
        setProfile(res.profile);
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
        <p className="mt-2 text-xs text-stone-500">
          Tus estadísticas históricas aparecen acá al terminar cada partida.
        </p>
      </section>
    </main>
  );
}
