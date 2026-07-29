import { useEffect, useMemo, useState } from 'react';
import { useSessionStore } from '../state/sessionStore';

type Incident = {
  code: string;
  title: string;
  category: string;
  severity: string;
  status: string;
  frequency: number;
  players: string[];
  games: string[];
  first_seen_at: string;
  last_seen_at: string;
  first_build: string;
  last_build: string;
};

const statuses = ['new', 'confirmed', 'investigating', 'duplicate', 'fixed', 'retest', 'closed', 'wont-fix'];
const severities = ['BLOCKER', 'CRITICAL', 'MAJOR', 'MINOR'];

export function AdminPlaytestPage() {
  const adminToken = useSessionStore((s) => s.adminToken);
  const [token, setToken] = useState(adminToken ?? '');
  const [data, setData] = useState<any>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<any>(null);
  const [filters, setFilters] = useState({ severity: '', category: '', status: '', build: '' });
  const [note, setNote] = useState('');
  const [msg, setMsg] = useState('');

  const headers = useMemo(() => ({ 'content-type': 'application/json', 'x-admin-token': token }), [token]);

  async function load() {
    const qs = new URLSearchParams(Object.entries(filters).filter(([, v]) => v));
    const res = await fetch(`/api/admin/playtest?${qs}`, { headers });
    if (!res.ok) throw new Error('No autorizado o error de panel');
    setData(await res.json());
  }

  async function loadDetail(code: string) {
    setSelected(code);
    const res = await fetch(`/api/admin/playtest/incidents/${code}`, { headers });
    setDetail(await res.json());
  }

  async function triage(code: string, status?: string, severity?: string) {
    await fetch(`/api/admin/playtest/incidents/${code}`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify({ status, severity, note }),
    });
    setNote('');
    await load();
    await loadDetail(code);
  }

  async function exportBacklog() {
    const res = await fetch('/api/admin/playtest/export', { method: 'POST', headers });
    setMsg(JSON.stringify(await res.json()));
  }

  async function purge() {
    const res = await fetch('/api/admin/playtest/purge', {
      method: 'POST',
      headers,
      body: JSON.stringify({ keep_confirmed: true, delete_attachments: false }),
    });
    setMsg(JSON.stringify(await res.json()));
    await load();
  }

  useEffect(() => {
    if (token) void load().catch((err) => setMsg(err.message));
  }, []);

  return (
    <main className="min-h-screen bg-war-950 p-5 text-stone-100">
      <header className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl text-gold-300">PLAYTEST</h1>
          <p className="text-sm text-stone-400">
            {data ? `${data.status.active ? 'Activo' : 'Inactivo'} · ${data.status.build} · ${data.status.env} · sesiones ${data.sessions} · partidas ${data.games}` : 'Sin cargar'}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <input value={token} onChange={(e) => setToken(e.target.value)} placeholder="Admin token" className="rounded border border-war-700 bg-war-900 px-3 py-2 text-sm" />
          <button onClick={() => { useSessionStore.getState().setAdminToken(token); void load(); }} className="rounded bg-gold-500 px-3 py-2 text-sm font-bold text-war-950">Cargar</button>
          <button onClick={exportBacklog} className="rounded border border-war-600 px-3 py-2 text-sm">Exportar backlog</button>
          <button onClick={purge} className="rounded border border-war-600 px-3 py-2 text-sm">Purgar antiguos</button>
        </div>
      </header>

      <section className="mb-4 flex flex-wrap gap-2">
        <select value={filters.severity} onChange={(e) => setFilters({ ...filters, severity: e.target.value })} className="rounded bg-war-900 px-2 py-2 text-sm">
          <option value="">Severidad</option>{severities.map((s) => <option key={s}>{s}</option>)}
        </select>
        <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })} className="rounded bg-war-900 px-2 py-2 text-sm">
          <option value="">Estado</option>{statuses.map((s) => <option key={s}>{s}</option>)}
        </select>
        <input value={filters.category} onChange={(e) => setFilters({ ...filters, category: e.target.value })} placeholder="Categoría" className="rounded bg-war-900 px-2 py-2 text-sm" />
        <input value={filters.build} onChange={(e) => setFilters({ ...filters, build: e.target.value })} placeholder="Build" className="rounded bg-war-900 px-2 py-2 text-sm" />
        <button onClick={() => void load()} className="rounded border border-war-600 px-3 py-2 text-sm">Filtrar</button>
      </section>

      {msg && <p className="mb-3 rounded border border-war-700 bg-war-900 p-2 text-xs text-stone-300">{msg}</p>}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_420px]">
        <section className="overflow-x-auto rounded-lg border border-war-700">
          <table className="w-full text-left text-sm">
            <thead className="bg-war-900 text-xs uppercase text-stone-400">
              <tr><th className="p-2">ID</th><th>Título</th><th>Sev</th><th>Estado</th><th>Freq</th><th>Build</th><th>Última</th></tr>
            </thead>
            <tbody>
              {(data?.incidents ?? []).map((i: Incident) => (
                <tr key={i.code} className={`border-t border-war-800 ${selected === i.code ? 'bg-war-800' : ''}`} onClick={() => void loadDetail(i.code)}>
                  <td className="p-2 font-mono text-gold-300">{i.code}</td>
                  <td>{i.title}</td>
                  <td>{i.severity}</td>
                  <td>{i.status}</td>
                  <td>{i.frequency}</td>
                  <td>{i.last_build}</td>
                  <td>{i.last_seen_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <aside className="rounded-lg border border-war-700 bg-war-900 p-3 text-sm">
          {!detail ? <p className="text-stone-400">Seleccioná un incidente.</p> : (
            <>
              <h2 className="font-display text-xl text-gold-300">{detail.incident.code}</h2>
              <p className="mt-1">{detail.incident.title}</p>
              <p className="mt-2 text-xs text-stone-400">Ocurrencias: {detail.occurrences.length} · Adjuntos: {detail.attachments.length}</p>
              <textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Nota de triage" className="mt-3 h-20 w-full rounded border border-war-700 bg-war-950 p-2" />
              <div className="mt-2 flex flex-wrap gap-2">
                {statuses.map((s) => <button key={s} onClick={() => void triage(detail.incident.code, s)} className="rounded border border-war-600 px-2 py-1 text-xs">{s}</button>)}
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                {severities.map((s) => <button key={s} onClick={() => void triage(detail.incident.code, undefined, s)} className="rounded border border-war-600 px-2 py-1 text-xs">{s}</button>)}
              </div>
              <h3 className="mt-4 font-bold">Últimas ocurrencias</h3>
              <pre className="mt-2 max-h-64 overflow-auto rounded bg-war-950 p-2 text-xs">{JSON.stringify(detail.occurrences.slice(0, 3), null, 2)}</pre>
              <h3 className="mt-4 font-bold">Action trail</h3>
              <pre className="mt-2 max-h-64 overflow-auto rounded bg-war-950 p-2 text-xs">{JSON.stringify(detail.trail.slice(0, 10), null, 2)}</pre>
            </>
          )}
        </aside>
      </div>
    </main>
  );
}
