import { useGameStore } from '../../state/gameStore';
import { useSessionStore } from '../../state/sessionStore';
import { colorValue } from '../../utils/playerColors';
import { PlayerAvatar } from '../players/PlayerAvatar';

const PHASE_LABEL: Record<string, string> = {
  reinforcement: '🪖 REFUERZOS',
  attack: '⚔️ ATAQUE',
  fortify: '🛡️ REAGRUPE',
};

/**
 * HUD superior estilo AoE2: en menos de dos segundos se responde quién juega,
 * qué fase es y cómo viene cada ejército (territorios, tropas, conexión).
 */
export function TopHud() {
  const players = useGameStore((s) => s.players);
  const territories = useGameStore((s) => s.territories);
  const turn = useGameStore((s) => s.turn);
  const stage = useGameStore((s) => s.stage);
  const placementDone = useGameStore((s) => s.placementDone);
  const currentPlayerId = useGameStore((s) => s.currentPlayerId);
  const hasPactWith = useGameStore((s) => s.hasPactWith);
  const session = useSessionStore((s) => s.session);

  const currentId = currentPlayerId();
  const combatants = players.filter(
    (p) => (p.role === 'player' || p.role === 'ai_player') && !p.eliminated,
  );
  const inPlacement = stage === 'placement_1' || stage === 'placement_2';

  const statsFor = (pid: string) => {
    let terr = 0;
    let troops = 0;
    for (const t of Object.values(territories)) {
      if (t.owner_player_id === pid) {
        terr += 1;
        troops += t.armies;
      }
    }
    return { terr, troops };
  };

  return (
    <header
      className="z-20 flex min-h-[54px] flex-wrap items-center gap-2 border-b-2 border-gold-600/70 bg-war-950 px-3 py-1.5"
      data-testid="top-hud"
    >
      <span className="font-display whitespace-nowrap text-sm font-bold tracking-widest text-gold-400">
        ⚔️ TEG LOPDA
      </span>

      <div className="flex min-w-0 flex-1 flex-wrap items-center justify-center gap-1.5" data-testid="hud-players">
        {combatants.map((p) => {
          const active = p.id === currentId;
          const me = p.id === session?.playerId;
          const { terr, troops } = statsFor(p.id);
          const done = inPlacement && placementDone.includes(p.id);
          return (
            <div
              key={p.id}
              data-testid={`hud-player-${p.nickname}`}
              className={`flex items-center gap-1.5 rounded-lg border px-2 py-1 transition-all ${
                active
                  ? 'scale-105 border-transparent bg-war-800 shadow-lg ring-2'
                  : 'border-war-700 bg-war-900/80 opacity-80'
              }`}
              style={active ? { boxShadow: `0 0 14px ${colorValue(p.color)}55`, ['--tw-ring-color' as string]: colorValue(p.color) } : undefined}
            >
              {active && <span className="animate-pulse text-xs" aria-label="jugador activo">👑</span>}
              <PlayerAvatar avatarAssetId={p.avatar_asset_id} role={p.role} color={p.color} size="sm" />
              <div className="min-w-0 leading-tight">
                <p className="max-w-24 truncate text-xs font-bold" style={{ color: colorValue(p.color) }}>
                  {p.nickname}{me ? ' (vos)' : ''}
                </p>
                <p className="text-[10px] text-stone-400">
                  🗺️{terr} · 🪖{troops}
                  {inPlacement && <span className={done ? 'text-emerald-400' : 'text-amber-400'}> {done ? '✓' : '…'}</span>}
                </p>
              </div>
              <span
                className="text-[9px]"
                title={p.presence === 'online' ? 'conectado' : p.presence === 'reconnecting' ? 'reconectando' : 'desconectado'}
              >
                {p.presence === 'online' ? '🟢' : p.presence === 'reconnecting' ? '🟡' : '⚫'}
              </span>
              {p.role === 'ai_player' && <span className="rounded bg-war-700 px-1 text-[9px]" title="Jugador IA">🤖</span>}
              {!me && hasPactWith(p.id) && <span className="text-[10px]" title="Pacto de no agresión vigente">🤝</span>}
            </div>
          );
        })}
      </div>

      <div className="flex items-center gap-2 whitespace-nowrap" data-testid="hud-phase">
        {inPlacement ? (
          <span className="rounded-lg border border-amber-600 bg-amber-950/70 px-2.5 py-1 text-xs font-bold text-amber-300">
            🪖 COLOCACIÓN {stage === 'placement_1' ? 'I' : 'II'}
          </span>
        ) : turn ? (
          <span className="rounded-lg border border-war-600 bg-war-800 px-2.5 py-1 text-xs font-bold text-stone-200">
            T{turn.turn_number} · {PHASE_LABEL[turn.phase] ?? turn.phase}
          </span>
        ) : null}
      </div>
    </header>
  );
}
