import { useEffect, useRef, useState } from 'react';
import type { Profile } from '@teg/contracts';
import { api } from '../../services/api/apiClient';

const EVENT_LABEL: Record<string, string> = {
  'game.started': '🎬 Saludo al arrancar la partida',
  'territory.conquered': '🚩 Cuando le conquisto un país',
  'player.eliminated': '💀 Cuando lo elimino',
  'attack.resolved': '⚔️ Cuando resolvemos un combate',
};

interface TauntView {
  id: string;
  target_profile_id: string;
  event_type: string;
  audio_url: string;
}

/**
 * Estudio de audios: grabá desde el micrófono (máx 10 s) o subí un archivo,
 * contra cada rival y por tipo de evento. Se guarda en tu perfil para siempre.
 */
export function TauntStudio({ profileToken, onClose }: { profileToken: string; onClose: () => void }) {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [me, setMe] = useState<Profile | null>(null);
  const [taunts, setTaunts] = useState<TauntView[]>([]);
  const [target, setTarget] = useState<string>('');
  const [eventType, setEventType] = useState<string>('territory.conquered');
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const stopTimerRef = useRef<number | null>(null);

  async function refresh() {
    const res = await fetch(`/api/profile/${encodeURIComponent(profileToken)}/taunts`);
    if (res.ok) setTaunts((await res.json()).taunts);
  }

  useEffect(() => {
    api.resolveProfile(profileToken).then((r) => setMe(r.profile)).catch(() => setError('Perfil inválido'));
    // la lista del grupo se sirve de los perfiles públicos de la partida/grupo
    fetch('/api/profile-group')
      .then((r) => (r.ok ? r.json() : { profiles: [] }))
      .then((r) => setProfiles(r.profiles ?? []))
      .catch(() => {});
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profileToken]);

  const rivals = profiles.filter((p) => p.id !== me?.id);

  useEffect(() => {
    if (!target && rivals.length > 0) setTarget(rivals[0].id);
  }, [rivals, target]);

  async function upload(blob: Blob, ext: string) {
    setBusy(true);
    setError(null);
    try {
      const params = new URLSearchParams({ target_profile_id: target, event_type: eventType, ext });
      const res = await fetch(`/api/profile/${encodeURIComponent(profileToken)}/taunts?${params}`, {
        method: 'POST',
        body: blob,
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail?.message ?? `Error HTTP ${res.status}`);
      }
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar el audio');
    } finally {
      setBusy(false);
    }
  }

  async function startRecording() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      chunksRef.current = [];
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        if (blob.size > 0) void upload(blob, 'webm');
      };
      recorder.start();
      recorderRef.current = recorder;
      setRecording(true);
      // tope de 10 segundos: los audios cortos pegan más y el disco lo agradece
      stopTimerRef.current = window.setTimeout(() => stopRecording(), 10_000);
    } catch {
      setError('No se pudo acceder al micrófono. Podés subir un archivo.');
    }
  }

  function stopRecording() {
    if (stopTimerRef.current) window.clearTimeout(stopTimerRef.current);
    recorderRef.current?.stop();
    recorderRef.current = null;
    setRecording(false);
  }

  async function onFile(file: File | null) {
    if (!file) return;
    const ext = file.name.toLowerCase().endsWith('.mp3') ? 'mp3'
      : file.name.toLowerCase().endsWith('.ogg') ? 'ogg' : 'webm';
    await upload(file, ext);
  }

  async function removeTaunt(id: string) {
    await fetch(`/api/profile/${encodeURIComponent(profileToken)}/taunts/${id}`, { method: 'DELETE' });
    await refresh();
  }

  const rivalName = (id: string) => profiles.find((p) => p.id === id)?.nickname ?? '?';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-war-950/80 p-4 backdrop-blur-md">
      <div className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-2xl border border-war-700 bg-war-900 p-5 shadow-2xl">
        <div className="flex items-center justify-between border-b border-war-700 pb-3">
          <div>
            <h3 className="font-display text-lg font-bold text-gold-400">🎙️ TUS AUDIOS DE GUERRA</h3>
            <p className="text-xs text-stone-400">
              Se reproducen automáticamente cuando pasa el evento contra ese rival. Para siempre, en todas las partidas.
            </p>
          </div>
          <button onClick={onClose} className="text-lg font-bold text-stone-400 hover:text-stone-100">✕</button>
        </div>

        {error && <p role="alert" className="mt-3 text-sm text-red-400">{error}</p>}

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <label className="text-xs text-stone-400">
            Contra quién
            <select value={target} onChange={(e) => setTarget(e.target.value)} className="mt-1 w-full rounded border border-war-700 bg-war-800 px-3 py-2 text-sm text-stone-100">
              {rivals.map((p) => <option key={p.id} value={p.id}>{p.nickname}</option>)}
            </select>
          </label>
          <label className="text-xs text-stone-400">
            Cuándo suena
            <select value={eventType} onChange={(e) => setEventType(e.target.value)} className="mt-1 w-full rounded border border-war-700 bg-war-800 px-3 py-2 text-sm text-stone-100">
              {Object.entries(EVENT_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </label>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          {!recording ? (
            <button
              onClick={startRecording}
              disabled={busy || !target}
              data-testid="record-taunt"
              className="rounded-xl bg-red-600 px-4 py-2 text-sm font-bold text-white hover:bg-red-500 disabled:opacity-30"
            >
              ⏺️ Grabar (máx 10 s)
            </button>
          ) : (
            <button onClick={stopRecording} className="animate-pulse rounded-xl bg-red-700 px-4 py-2 text-sm font-bold text-white">
              ⏹️ Grabando… tocá para cortar
            </button>
          )}
          <label className="cursor-pointer rounded-xl border border-war-700 px-4 py-2 text-sm text-stone-300 hover:border-gold-500">
            📁 Subir archivo
            <input type="file" accept=".mp3,.ogg,.webm,audio/*" className="hidden"
              onChange={(e) => void onFile(e.target.files?.[0] ?? null)} disabled={busy || !target} />
          </label>
          {busy && <span className="text-xs text-stone-400">Guardando…</span>}
        </div>

        <h4 className="mt-5 text-xs font-semibold tracking-wider text-stone-400">TUS AUDIOS GUARDADOS</h4>
        {taunts.length === 0 ? (
          <p className="mt-2 text-sm text-stone-500">Todavía no grabaste ninguno. Dale, que el viernes se viene.</p>
        ) : (
          <ul className="mt-2 space-y-1.5">
            {taunts.map((t) => (
              <li key={t.id} className="flex flex-wrap items-center gap-2 rounded-lg border border-war-700 bg-war-800/60 px-3 py-1.5 text-sm">
                <span className="font-semibold text-stone-200">→ {rivalName(t.target_profile_id)}</span>
                <span className="text-xs text-stone-400">{EVENT_LABEL[t.event_type] ?? t.event_type}</span>
                <span className="ml-auto flex items-center gap-2">
                  <audio src={t.audio_url} controls preload="none" className="h-8 w-40" />
                  <button onClick={() => void removeTaunt(t.id)} className="text-xs text-red-400 hover:text-red-300">🗑️</button>
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
