import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import type { PublicPlayer } from '@teg/contracts';
import { useSessionStore } from '../state/sessionStore';
import { assetRegistry } from '../services/assets/AssetRegistry';
import { colorValue } from '../utils/playerColors';

interface ReplayIndex {
  game: { name: string; game_mode?: string | null };
  players: PublicPlayer[];
  turns: number[];
}

interface ReplayTurn {
  turn_number: number;
  territories: Record<string, { territory_id?: string; owner_player_id: string | null; armies: number }>;
  events: {
    event_id: string;
    event_type: string;
    actor_id?: string | null;
    target_id?: string | null;
    payload: Record<string, unknown>;
  }[];
}

const SPEEDS = [1500, 800, 400];

/** Visor de partida terminada: el mapa turno a turno con sus combates. */
export function ReplayPage() {
  const { code = '' } = useParams();
  const session = useSessionStore((s) => s.session);
  const containerRef = useRef<HTMLDivElement>(null);
  const [index, setIndex] = useState<ReplayIndex | null>(null);
  const [turnData, setTurnData] = useState<ReplayTurn | null>(null);
  const [cursor, setCursor] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const cache = useRef<Map<number, ReplayTurn>>(new Map());

  const token = session?.code === code ? session.token : null;

  useEffect(() => {
    if (!token) return;
    fetch(`/api/join/${code}/${encodeURIComponent(token)}/replay`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('replay no disponible'))))
      .then(setIndex)
      .catch(() => setError('No se pudo cargar el replay de esta partida.'));
  }, [code, token]);

  const loadTurn = useCallback(
    async (turnNumber: number) => {
      if (!token) return;
      const cached = cache.current.get(turnNumber);
      if (cached) {
        setTurnData(cached);
        return;
      }
      const res = await fetch(`/api/join/${code}/${encodeURIComponent(token)}/replay/${turnNumber}`);
      if (!res.ok) return;
      const data: ReplayTurn = await res.json();
      cache.current.set(turnNumber, data);
      setTurnData(data);
    },
    [code, token],
  );

  useEffect(() => {
    const turn = index?.turns[cursor];
    if (turn !== undefined) void loadTurn(turn);
  }, [index, cursor, loadTurn]);

  // auto-play
  useEffect(() => {
    if (!playing || !index) return;
    const t = window.setInterval(() => {
      setCursor((c) => {
        if (c + 1 >= index.turns.length) {
          setPlaying(false);
          return c;
        }
        return c + 1;
      });
    }, SPEEDS[speed]);
    return () => window.clearInterval(t);
  }, [playing, speed, index]);

  // cargar el SVG del mapa una vez
  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!assetRegistry.loaded) await assetRegistry.load();
      const mode = (index?.game.game_mode ?? 'classic_26') as never;
      const url = assetRegistry.mapUrl(mode);
      if (!url || !containerRef.current) return;
      const res = await fetch(url);
      const text = await res.text();
      if (cancelled || !containerRef.current) return;
      containerRef.current.innerHTML = text;
      const svg = containerRef.current.querySelector('svg');
      if (svg) {
        svg.setAttribute('width', '100%');
        svg.setAttribute('height', '100%');
      }
    }
    if (index) void load();
    return () => {
      cancelled = true;
    };
  }, [index]);

  // pintar el estado del turno sobre el SVG
  useEffect(() => {
    const container = containerRef.current;
    if (!container || !turnData || !index) return;
    const svg = container.querySelector('svg');
    if (!svg) return;
    const byId = new Map(index.players.map((p) => [p.id, p]));
    let overlay = svg.querySelector<SVGGElement>('#replay-overlay');
    if (!overlay) {
      overlay = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      overlay.setAttribute('id', 'replay-overlay');
      svg.appendChild(overlay);
    }
    overlay.innerHTML = '';
    svg.querySelectorAll<SVGPathElement>('.territory').forEach((path) => {
      const id = path.getAttribute('id');
      const t = id ? turnData.territories[id] : undefined;
      const owner = t?.owner_player_id ? byId.get(t.owner_player_id) : undefined;
      path.style.fill = owner ? colorValue(owner.color) : 'rgba(30, 35, 45, 0.85)';
      path.style.fillOpacity = '0.75';
      if (t && id) {
        try {
          const bbox = path.getBBox();
          const cx = bbox.x + bbox.width / 2;
          const cy = bbox.y + bbox.height / 2;
          const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
          circle.setAttribute('cx', String(cx));
          circle.setAttribute('cy', String(cy));
          circle.setAttribute('r', '38');
          circle.setAttribute('fill', '#0f172a');
          circle.setAttribute('fill-opacity', '0.9');
          circle.setAttribute('stroke', owner ? colorValue(owner.color) : '#94a3b8');
          circle.setAttribute('stroke-width', '4');
          overlay!.appendChild(circle);
          const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
          text.setAttribute('x', String(cx));
          text.setAttribute('y', String(cy + 14));
          text.setAttribute('text-anchor', 'middle');
          text.setAttribute('fill', '#f8fafc');
          text.setAttribute('font-size', '40');
          text.setAttribute('font-weight', '900');
          text.textContent = String(t.armies);
          overlay!.appendChild(text);
        } catch {
          // territorio fuera de pantalla: sin insignia
        }
      }
    });
  }, [turnData, index]);

  if (!token) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-3 p-8">
        <p className="text-stone-400">Para ver el replay entrá primero a la partida con tu link.</p>
        <Link to="/" className="text-gold-400 underline">Volver al inicio</Link>
      </main>
    );
  }
  if (error) {
    return <main className="p-8 text-red-400">{error}</main>;
  }
  if (!index) {
    return <main className="p-8 text-stone-400">Cargando replay…</main>;
  }

  const nick = (id?: string | null) =>
    index.players.find((p) => p.id === id)?.nickname ?? '???';

  const combatEvents = (turnData?.events ?? []).filter((e) =>
    ['attack.resolved', 'territory.conquered', 'player.eliminated', 'cards.traded', 'pact.broken'].includes(e.event_type),
  );

  return (
    <main className="mx-auto flex h-screen max-w-6xl flex-col gap-3 p-4" data-testid="replay-page">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="font-display text-xl font-bold text-gold-400">
          🎬 Replay — {index.game.name}
        </h1>
        <Link to={`/game/${code}`} className="text-sm text-stone-400 hover:text-gold-400">
          ← volver a la partida
        </Link>
      </header>

      <div className="flex flex-wrap items-center justify-center gap-2 rounded-xl border border-war-700 bg-war-900 p-2">
        <button onClick={() => { setPlaying(false); setCursor(0); }} className="rounded-lg border border-war-700 px-3 py-1.5 text-sm hover:border-gold-500">⏮</button>
        <button onClick={() => { setPlaying(false); setCursor((c) => Math.max(0, c - 1)); }} className="rounded-lg border border-war-700 px-3 py-1.5 text-sm hover:border-gold-500">◀</button>
        <button
          onClick={() => setPlaying((p) => !p)}
          data-testid="replay-play"
          className="rounded-lg bg-gold-500 px-4 py-1.5 text-sm font-bold text-war-950 hover:bg-gold-400"
        >
          {playing ? '⏸ Pausa' : '▶ Reproducir'}
        </button>
        <button onClick={() => { setPlaying(false); setCursor((c) => Math.min(index.turns.length - 1, c + 1)); }} className="rounded-lg border border-war-700 px-3 py-1.5 text-sm hover:border-gold-500">▶</button>
        <button onClick={() => { setPlaying(false); setCursor(index.turns.length - 1); }} className="rounded-lg border border-war-700 px-3 py-1.5 text-sm hover:border-gold-500">⏭</button>
        <button
          onClick={() => setSpeed((s) => (s + 1) % SPEEDS.length)}
          className="rounded-lg border border-war-700 px-3 py-1.5 text-xs text-stone-300 hover:border-gold-500"
        >
          velocidad ×{[1, 2, 4][speed]}
        </button>
        <span className="text-sm text-stone-300">
          Turno <strong className="text-gold-400">{index.turns[cursor]}</strong> / {index.turns[index.turns.length - 1]}
        </span>
        <input
          type="range"
          min={0}
          max={Math.max(0, index.turns.length - 1)}
          value={cursor}
          onChange={(e) => { setPlaying(false); setCursor(Number(e.target.value)); }}
          className="w-full max-w-md accent-amber-500"
          aria-label="Línea de tiempo de turnos"
        />
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-3 lg:grid-cols-[1fr_280px]">
        <div className="min-h-0 overflow-hidden rounded-xl border border-war-700 bg-war-900">
          <div ref={containerRef} className="h-full w-full" />
        </div>
        <aside className="min-h-0 overflow-y-auto rounded-xl border border-war-700 bg-war-900 p-3">
          <h2 className="mb-2 text-xs font-semibold tracking-wider text-stone-400">EN ESTE TURNO</h2>
          {combatEvents.length === 0 ? (
            <p className="text-sm text-stone-500">Turno tranquilo: sin combates.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {combatEvents.map((e) => (
                <li key={e.event_id} className="rounded-lg border border-war-700 bg-war-950/60 p-2">
                  {e.event_type === 'attack.resolved' && (
                    <>
                      <p>
                        ⚔️ <strong>{nick(e.actor_id)}</strong> vs <strong>{nick(e.target_id)}</strong>
                      </p>
                      <p className="mt-0.5 text-xs text-stone-400">
                        🎲 {String((e.payload.attacker_dice as number[] | undefined)?.join(' ') ?? '')} contra{' '}
                        {String((e.payload.defender_dice as number[] | undefined)?.join(' ') ?? '')} — bajas{' '}
                        {String(e.payload.attacker_losses)} / {String(e.payload.defender_losses)}
                      </p>
                    </>
                  )}
                  {e.event_type === 'territory.conquered' && (
                    <p>🚩 <strong>{nick(e.actor_id)}</strong> conquistó territorio de <strong>{nick(e.target_id)}</strong></p>
                  )}
                  {e.event_type === 'player.eliminated' && (
                    <p>💀 <strong>{nick(e.target_id)}</strong> fue eliminado por <strong>{nick(e.actor_id)}</strong></p>
                  )}
                  {e.event_type === 'cards.traded' && (
                    <p>🃏 <strong>{nick(e.actor_id)}</strong> canjeó tarjetas (+{String(e.payload.value)})</p>
                  )}
                  {e.event_type === 'pact.broken' && (
                    <p>🗡️ <strong>{nick(e.actor_id)}</strong> rompió el pacto con <strong>{nick(e.target_id)}</strong></p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </aside>
      </div>
    </main>
  );
}
