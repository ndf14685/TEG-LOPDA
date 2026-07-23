import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { wsClient } from '../services/websocket/wsClient';
import { bindWsToStores } from '../services/websocket/bindStores';
import { useSessionStore } from '../state/sessionStore';
import { useGameStore } from '../state/gameStore';
import { useConnectionStore } from '../state/connectionStore';
import { GameMap } from '../components/map/GameMap';
import { AICommentatorPanel } from '../components/ai-commentator/AICommentatorPanel';
import { ChatPanel } from '../components/chat/ChatPanel';
import { SoundboardBar } from '../components/audio/SoundboardBar';
import { ConnectionBanner } from '../components/ConnectionBanner';
import { PlayerAvatar } from '../components/players/PlayerAvatar';
import { PLAYER_COLOR_VAR } from '../utils/playerColors';
import { SLICE_MAP } from '@teg/contracts';

const PHASE_LABEL: Record<string, string> = {
  deploy: 'Refuerzos',
  attack: 'Ataque',
  fortify: 'Reagrupe',
  none: '—',
};

export function GamePage() {
  const { gameId = '' } = useParams();
  const navigate = useNavigate();
  const session = useSessionStore((s) => s.session);
  const restore = useSessionStore((s) => s.restore);
  const snapshot = useGameStore((s) => s.snapshot);
  const selectedId = useGameStore((s) => s.selectedTerritoryId);
  const playerById = useGameStore((s) => s.playerById);
  const syncState = useConnectionStore((s) => s.syncState);

  useEffect(() => {
    if (!session && !restore(gameId)) navigate('/');
  }, [session, gameId, restore, navigate]);

  useEffect(() => {
    if (!session) return;
    bindWsToStores();
    wsClient.connect(session.sessionId);
    // si entramos directo (refresh), el server manda snapshot al abrir; si ya estaba abierto, lo pedimos
    wsClient.send({ type: 'sync.request' });
  }, [session]);

  if (!session) return null;

  const current = playerById(snapshot?.currentPlayerId);
  const selected = snapshot?.territories.find((t) => t.id === selectedId);
  const selectedDef = SLICE_MAP.find((t) => t.id === selectedId);
  const selectedOwner = selected ? playerById(selected.ownerId) : undefined;
  const actionsBlocked = syncState !== 'synced';

  return (
    <main className="flex h-screen flex-col" data-testid="game-board">
      <ConnectionBanner />

      {/* fila principal: jugadores | mapa | turno+IA */}
      <div className="grid min-h-0 flex-1 grid-cols-1 gap-3 p-3 lg:grid-cols-[230px_1fr_300px]">
        <aside className="hidden min-h-0 flex-col gap-2 overflow-y-auto lg:flex">
          <h2 className="text-xs font-semibold tracking-wider text-stone-400">EJÉRCITOS</h2>
          {(snapshot?.players ?? []).filter((p) => p.role !== 'spectator').map((p) => {
            const owned = snapshot?.territories.filter((t) => t.ownerId === p.id) ?? [];
            const armies = owned.reduce((sum, t) => sum + t.armies, 0);
            return (
              <div key={p.id} className={`rounded-lg border bg-war-900 px-3 py-2 ${snapshot?.currentPlayerId === p.id ? 'border-gold-500' : 'border-war-700'}`}>
                <div className="flex items-center gap-2">
                  <PlayerAvatar avatarId={p.avatarId} color={p.color} size="sm" />
                  <span className="truncate text-sm font-semibold" style={{ color: PLAYER_COLOR_VAR[p.color] }}>{p.nickname}</span>
                  {p.isAI && <span className="rounded bg-war-700 px-1 text-[10px]">🤖 IA</span>}
                </div>
                <p className="mt-1 text-xs text-stone-400">{owned.length} territorios · {armies} ejércitos</p>
              </div>
            );
          })}
        </aside>

        <section className="relative min-h-0 rounded-xl border border-war-700 bg-war-900">
          <GameMap />
          {actionsBlocked && (
            <div className="absolute inset-0 z-10 flex items-center justify-center rounded-xl bg-war-950/70">
              <p className="rounded-lg bg-war-800 px-4 py-2 text-sm">⏳ Sincronizando — acciones bloqueadas</p>
            </div>
          )}
        </section>

        <aside className="flex min-h-0 flex-col gap-3 overflow-y-auto">
          <div className="rounded-lg border border-war-700 bg-war-900 p-3" data-testid="turn-panel">
            <h2 className="mb-1 text-xs font-semibold tracking-wider text-stone-400">TURNO</h2>
            {current ? (
              <p className="text-sm">
                Juega <strong style={{ color: PLAYER_COLOR_VAR[current.color] }}>{current.nickname}</strong>
                {current.id === session.playerId && <span className="text-gold-400"> — ¡sos vos!</span>}
              </p>
            ) : (
              <p className="text-sm text-stone-500">…</p>
            )}
            <p className="text-xs text-stone-400">Fase: {PHASE_LABEL[snapshot?.phase ?? 'none']}</p>
          </div>

          {selected && selectedDef && (
            <div className="rounded-lg border border-war-700 bg-war-900 p-3" data-testid="territory-detail">
              <h2 className="mb-1 text-xs font-semibold tracking-wider text-stone-400">TERRITORIO</h2>
              <p className="text-sm font-semibold">{selectedDef.name}</p>
              <p className="text-xs text-stone-400">
                {selectedOwner ? <>de <span style={{ color: PLAYER_COLOR_VAR[selectedOwner.color] }}>{selectedOwner.nickname}</span></> : 'neutral'}
                {' · '}{selected.armies} ejércitos · {selectedDef.continent}
              </p>
              <p className="mt-1 text-xs text-stone-500">Fronteras: {selectedDef.borders.map((b) => SLICE_MAP.find((t) => t.id === b)?.name).join(', ')}</p>
            </div>
          )}

          <AICommentatorPanel />
        </aside>
      </div>

      {/* barra inferior: soundboard + chat */}
      <footer className="grid gap-3 border-t border-war-700 bg-war-900/60 p-3 lg:grid-cols-[1fr_380px]">
        <div>
          <h2 className="mb-1.5 text-xs font-semibold tracking-wider text-stone-400">BARDEO RÁPIDO</h2>
          <SoundboardBar />
        </div>
        <ChatPanel compact />
      </footer>
    </main>
  );
}
