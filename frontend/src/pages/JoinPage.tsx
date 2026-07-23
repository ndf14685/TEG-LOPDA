import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import type { JoinPreviewResponse } from '@teg/contracts';
import { api, ApiRequestError } from '../services/api/apiClient';
import { audioService } from '../services/audio/AudioService';
import { useSessionStore } from '../state/sessionStore';
import { PlayerAvatar } from '../components/players/PlayerAvatar';
import { PLAYER_COLOR_LABEL } from '../utils/playerColors';

const ERROR_TEXT: Record<string, string> = {
  NOT_FOUND: 'Este link no corresponde a ninguna partida (o fue revocado). Pedile al admin uno nuevo.',
  AUTH_FAILED: 'El link no es válido. Alguien te quiere afuera 👀',
  RATE_LIMITED: 'Demasiados intentos. Respirá y probá de nuevo en un rato.',
};

export function JoinPage() {
  const { code = '', token = '' } = useParams();
  const navigate = useNavigate();
  const [preview, setPreview] = useState<JoinPreviewResponse | null>(null);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [nickname, setNickname] = useState('');
  const [audioTested, setAudioTested] = useState(false);
  const [entering, setEntering] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api.joinPreview(code, token)
      .then((res) => {
        if (cancelled) return;
        setPreview(res);
        setNickname(res.player.nickname);
      })
      .catch((err) => {
        if (cancelled) return;
        setErrorCode(err instanceof ApiRequestError ? err.code : 'INTERNAL_ERROR');
      });
    return () => { cancelled = true; };
  }, [code, token]);

  function testAudio() {
    audioService.unlock();
    audioService.playTestFanfare();
    setAudioTested(true);
  }

  async function enter() {
    if (!preview) return;
    audioService.unlock();
    setEntering(true);
    try {
      const editable = preview.player.nickname_editable;
      const chosen = nickname.trim();
      const confirmed = await api.joinConfirm(code, token, editable && chosen ? chosen : null);
      useSessionStore.getState().setSession({
        code,
        gameId: confirmed.game.id,
        token,
        playerId: confirmed.player.id,
        nickname: confirmed.player.nickname,
        role: confirmed.player.role,
      });
      navigate(`/lobby/${code}`);
    } catch (err) {
      setErrorCode(err instanceof ApiRequestError ? err.code : 'INTERNAL_ERROR');
    } finally {
      setEntering(false);
    }
  }

  if (errorCode) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-6 text-center">
        <span className="text-6xl">🚫</span>
        <h1 className="font-display text-2xl font-bold text-red-400">Acceso denegado</h1>
        <p role="alert" data-testid="join-error" className="max-w-md text-stone-300">
          {ERROR_TEXT[errorCode] ?? 'Algo salió mal. Reintentá en un rato.'}
        </p>
      </main>
    );
  }

  if (!preview) {
    return <main className="flex min-h-screen items-center justify-center text-stone-400">Verificando credenciales…</main>;
  }

  const { player, game } = preview;

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-6">
      <h1 className="font-display text-3xl font-bold text-gold-400">Te estaban esperando</h1>

      <section data-testid="identity-card" className="w-full max-w-md rounded-xl border border-war-700 bg-war-900 p-6 text-center">
        <div className="mb-4 flex justify-center">
          <PlayerAvatar avatarAssetId={null} role={player.role} color={player.color} size="lg" />
        </div>
        <p className="text-lg font-semibold">{player.nickname}</p>
        <p className="text-sm text-stone-400">
          Partida: {game.name} · Rol: {player.role}
          {player.color && <> · Color: {PLAYER_COLOR_LABEL[player.color] ?? player.color}</>}
          {player.already_joined && <> · ya entraste antes</>}
        </p>

        <label className="mt-5 block text-left text-sm">
          <span className="mb-1 block text-stone-400">
            Tu apodo de guerra {player.nickname_editable ? '(editable)' : '(lo fijó el admin)'}
          </span>
          <input
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            maxLength={64}
            disabled={!player.nickname_editable}
            data-testid="nickname-input"
            className="w-full rounded border border-war-700 bg-war-800 px-3 py-2 outline-none focus:border-gold-500 disabled:opacity-60"
          />
        </label>

        <div className="mt-4 flex gap-2">
          <button onClick={testAudio} className="flex-1 rounded-lg border border-war-700 bg-war-800 px-4 py-2 text-sm hover:border-gold-500">
            {audioTested ? '🔊 ¿Se escuchó?' : '🔈 Probar audio'}
          </button>
          <button onClick={enter} disabled={entering || !nickname.trim()} data-testid="enter-lobby" className="flex-1 rounded-lg bg-gold-500 px-4 py-2 font-bold text-war-950 hover:bg-gold-400 disabled:opacity-40">
            Entrar a la sala →
          </button>
        </div>
      </section>

      <p className="text-xs text-stone-600">Preparate. Acá las alianzas duran menos que un ceasefire de WhatsApp.</p>
    </main>
  );
}
