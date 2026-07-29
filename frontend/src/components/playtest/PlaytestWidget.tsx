import { useEffect, useMemo, useState } from 'react';
import { playtestClient } from '../../services/playtest/playtestClient';

const categories = [
  'no-understood',
  'action-did-not-work',
  'incorrect-result',
  'desynchronization',
  'visual-problem',
  'connection-problem',
  'other',
];

const severities = ['impide seguir', 'dificulta jugar', 'molesto', 'detalle menor'];

export function PlaytestWidget() {
  const [active, setActive] = useState(playtestClient.active);
  const [open, setOpen] = useState(false);
  const [notice, setNotice] = useState(false);
  const [category, setCategory] = useState(categories[0]);
  const [description, setDescription] = useState('');
  const [expected, setExpected] = useState('');
  const [severity, setSeverity] = useState(severities[1]);
  const [image, setImage] = useState<string | null>(null);
  const [result, setResult] = useState('');
  const [error, setError] = useState('');
  const status = playtestClient.status;
  const buildLine = useMemo(() => status ? `${status.build} · ${status.env} · ${status.active ? 'activo' : 'inactivo'}` : '', [status]);

  useEffect(() => {
    const t = setInterval(() => setActive(playtestClient.active), 500);
    setNotice(playtestClient.active && sessionStorage.getItem('teg.playtest.notice') !== 'seen');
    return () => clearInterval(t);
  }, []);

  if (!active || location.pathname.startsWith('/admin/playtest')) return null;

  async function onPaste(e: React.ClipboardEvent) {
    const file = Array.from(e.clipboardData.files).find((f) => f.type.startsWith('image/'));
    if (!file) return;
    await readImage(file);
  }

  async function readImage(file: File) {
    setError('');
    if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) {
      setError('Formato inválido. Usá PNG, JPG o WebP.');
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      setError('La captura supera 2 MB.');
      return;
    }
    const data = await new Promise<string>((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result));
      reader.readAsDataURL(file);
    });
    setImage(data);
  }

  async function submit() {
    setError('');
    setResult('');
    if (!description.trim()) {
      setError('La descripción es obligatoria.');
      return;
    }
    try {
      const id = await playtestClient.reportManual({
        category,
        description: description.trim().slice(0, 2000),
        expected: expected.trim().slice(0, 1000),
        perceivedSeverity: severity as any,
        screenshotDataUrl: image,
      });
      setResult(`Reporte ${id} registrado.`);
      setDescription('');
      setExpected('');
      setImage(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo registrar el reporte.');
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-4 right-4 z-50 rounded-lg border border-gold-500/60 bg-war-900/95 px-3 py-2 text-sm font-bold text-gold-200 shadow-xl hover:bg-war-800"
      >
        🐞 Reportar problema
      </button>
      {notice && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-war-950/80 p-4">
          <section className="max-w-lg rounded-lg border border-gold-500/50 bg-war-900 p-5 text-stone-100">
            <h2 className="font-display text-xl text-gold-300">MODO DE PRUEBA ACTIVO</h2>
            <p className="mt-3 text-sm text-stone-300">
              Durante esta partida se registran errores técnicos, acciones del juego y reportes manuales para mejorar TEG-LOPDA.
            </p>
            <p className="mt-2 text-sm text-stone-400">No se graba audio ni Discord. No se guardan tokens completos ni objetivos secretos compartidos.</p>
            <p className="mt-3 text-xs text-stone-500">{buildLine}</p>
            <button
              className="mt-4 rounded bg-gold-500 px-4 py-2 font-bold text-war-950"
              onClick={() => { sessionStorage.setItem('teg.playtest.notice', 'seen'); setNotice(false); }}
            >
              Entendido
            </button>
          </section>
        </div>
      )}
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-war-950/80 p-4" onPaste={onPaste}>
          <section className="w-full max-w-xl rounded-lg border border-war-700 bg-war-900 p-5 text-stone-100">
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-display text-xl text-gold-300">Reportar problema</h2>
              <button className="rounded border border-war-600 px-2 py-1 text-sm" onClick={() => setOpen(false)}>Cerrar</button>
            </div>
            <p className="mt-1 text-xs text-stone-500">{buildLine}</p>
            <label className="mt-4 block text-sm">Categoría
              <select value={category} onChange={(e) => setCategory(e.target.value)} className="mt-1 w-full rounded border border-war-700 bg-war-800 px-3 py-2">
                {categories.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </label>
            <label className="mt-3 block text-sm">Descripción
              <textarea value={description} onChange={(e) => setDescription(e.target.value)} maxLength={2000} required className="mt-1 h-24 w-full rounded border border-war-700 bg-war-800 px-3 py-2" />
            </label>
            <label className="mt-3 block text-sm">Qué esperaba que ocurriera
              <textarea value={expected} onChange={(e) => setExpected(e.target.value)} maxLength={1000} className="mt-1 h-16 w-full rounded border border-war-700 bg-war-800 px-3 py-2" />
            </label>
            <label className="mt-3 block text-sm">Severidad percibida
              <select value={severity} onChange={(e) => setSeverity(e.target.value)} className="mt-1 w-full rounded border border-war-700 bg-war-800 px-3 py-2">
                {severities.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </label>
            <label className="mt-3 block text-sm">Captura opcional
              <input type="file" accept="image/png,image/jpeg,image/webp" onChange={(e) => e.target.files?.[0] && void readImage(e.target.files[0])} className="mt-1 w-full text-sm" />
            </label>
            <p className="mt-1 text-xs text-stone-500">También podés pegar una imagen desde el portapapeles. Máximo 2 MB.</p>
            {image && <p className="mt-2 text-xs text-green-300">Captura adjunta.</p>}
            {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
            {result && <p className="mt-3 text-sm text-green-300">{result}</p>}
            <button onClick={submit} className="mt-4 rounded bg-gold-500 px-4 py-2 font-bold text-war-950">Enviar reporte</button>
          </section>
        </div>
      )}
    </>
  );
}
