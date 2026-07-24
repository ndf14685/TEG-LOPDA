import { useGameStore } from '../../state/gameStore';
import { colorValue } from '../../utils/playerColors';
import { PlayerAvatar } from '../players/PlayerAvatar';

const CONFETTI_COLORS = ['#f59e0b', '#22c55e', '#3b82f6', '#ef4444', '#a855f7', '#eab308'];

function Confetti() {
  // 40 papelitos con posición/tempo pseudoaleatorios pero estables por render
  const pieces = Array.from({ length: 40 }, (_, i) => ({
    left: `${(i * 37) % 100}%`,
    background: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
    animationDuration: `${2.2 + ((i * 13) % 17) / 10}s`,
    animationDelay: `${((i * 7) % 20) / 10}s`,
  }));
  return (
    <>
      {pieces.map((style, i) => (
        <span key={i} className="teg-confetti" style={style} aria-hidden />
      ))}
    </>
  );
}

export function PostGameModal() {
  const finished = useGameStore((s) => s.finished);
  const finishedObjective = useGameStore((s) => s.finishedObjective);
  const trophies = useGameStore((s) => s.trophies);
  const playerById = useGameStore((s) => s.playerById);

  if (!finished) return null;

  const winner = finished.winnerPlayerId ? playerById(finished.winnerPlayerId) : undefined;
  const trophyEntries = trophies
    ? Object.entries(trophies).flatMap(([pid, list]) => list.map((t) => ({ pid, ...t })))
    : [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-war-950/95 p-4 backdrop-blur-lg">
      <Confetti />
      <div className="w-full max-w-2xl rounded-2xl border border-gold-500/50 bg-gradient-to-b from-war-900 via-war-950 to-stone-950 p-6 text-slate-100 shadow-2xl">
        {/* Encabezado */}
        <div className="text-center">
          <span className="text-6xl animate-bounce inline-block">🏆</span>
          <h1 className="mt-2 font-display text-3xl font-black tracking-wide text-gold-400">
            {winner ? `¡GANÓ ${winner.nickname.toUpperCase()}!` : 'SE TERMINÓ LA GUERRA'}
          </h1>
          <p className="mt-1 text-sm text-stone-400">
            {finished.turnsPlayed} turnos de estrategia, traición y puro bardo.
          </p>
        </div>

        {/* Ganador y cómo ganó (los trofeos reales llegan con las estadísticas) */}
        <div className="mt-6 flex flex-col items-center gap-3">
          <div className="flex w-full max-w-md flex-col items-center rounded-xl border border-gold-500/40 bg-gold-950/20 p-4 text-center">
            <span className="text-3xl">👑</span>
            <div className="my-2 flex items-center gap-2">
              <PlayerAvatar avatarAssetId={winner?.avatar_asset_id ?? null} color={winner?.color ?? null} role={winner?.role ?? 'player'} size="sm" />
              <span className="font-semibold text-sm" style={{ color: colorValue(winner?.color) }}>
                {winner?.nickname ?? 'Desconocido'}
              </span>
            </div>
            {finishedObjective ? (
              <>
                <p className="text-xs font-bold text-purple-300">🕵️ Cumplió su objetivo secreto</p>
                <p className="mt-1 text-sm font-bold text-gold-400">{finishedObjective.title}</p>
                <p className="mt-1 text-[11px] text-stone-400">{finishedObjective.description}</p>
              </>
            ) : (
              <p className="text-xs text-stone-400">Victoria por dominación total del mapa</p>
            )}
          </div>
        </div>

        {/* Trofeos absurdos REALES: cada uno respaldado por el event log */}
        {trophyEntries.length > 0 && (
          <div className="mt-5">
            <h2 className="mb-2 text-center text-xs font-semibold tracking-wider text-stone-400">
              🏅 TROFEOS DE LA NOCHE
            </h2>
            <div className="grid max-h-56 grid-cols-1 gap-2 overflow-y-auto sm:grid-cols-3">
              {trophyEntries.map((t) => {
                const p = playerById(t.pid);
                return (
                  <div key={`${t.pid}-${t.id}`} className="rounded-xl border border-war-700 bg-war-950/60 p-3 text-center">
                    <span className="text-2xl">{t.icon}</span>
                    <h3 className="mt-0.5 text-xs font-bold text-gold-400">{t.title}</h3>
                    <p className="text-sm font-semibold" style={{ color: colorValue(p?.color) }}>
                      {p?.nickname ?? '???'} <span className="text-xs text-stone-500">({t.value})</span>
                    </p>
                    <p className="mt-0.5 text-[10px] leading-tight text-stone-400">{t.blurb}</p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Botón de Salir */}
        <div className="mt-6 flex justify-center">
          <button
            onClick={() => (window.location.href = '/')}
            className="rounded-xl bg-gold-500 px-6 py-2.5 text-sm font-bold text-war-950 hover:bg-gold-400 transition"
          >
            Volver al Inicio ➔
          </button>
        </div>
      </div>
    </div>
  );
}
