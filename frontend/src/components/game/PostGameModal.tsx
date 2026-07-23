import { useGameStore } from '../../state/gameStore';
import { colorValue } from '../../utils/playerColors';
import { PlayerAvatar } from '../players/PlayerAvatar';

export function PostGameModal() {
  const finished = useGameStore((s) => s.finished);
  const players = useGameStore((s) => s.players);
  const playerById = useGameStore((s) => s.playerById);

  if (!finished) return null;

  const winner = finished.winnerPlayerId ? playerById(finished.winnerPlayerId) : undefined;
  const combatants = players.filter((p) => p.role === 'player' || p.role === 'admin' || p.role === 'ai_player');

  // Asignación humorística de trofeos
  const traitor = combatants[1 % combatants.length] ?? winner;
  const manco = combatants[combatants.length - 1] ?? winner;
  const muralla = combatants[0] ?? winner;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-war-950/95 p-4 backdrop-blur-lg">
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

        {/* Podio de Premios Humorísticos */}
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
          {/* Trofeo 1: El Conquistador */}
          <div className="flex flex-col items-center rounded-xl border border-gold-500/40 bg-gold-950/20 p-4 text-center">
            <span className="text-3xl">👑</span>
            <h3 className="mt-1 font-bold text-xs text-gold-400">EL CONQUISTADOR</h3>
            <div className="my-2 flex items-center gap-2">
              <PlayerAvatar avatarAssetId={winner?.avatar_asset_id ?? null} color={winner?.color ?? null} role={winner?.role ?? 'player'} size="sm" />
              <span className="font-semibold text-sm" style={{ color: colorValue(winner?.color) }}>
                {winner?.nickname ?? 'Desconocido'}
              </span>
            </div>
            <p className="text-[10px] text-stone-400">Dominio absoluto del tablero</p>
          </div>

          {/* Trofeo 2: El Manco de la Noche */}
          <div className="flex flex-col items-center rounded-xl border border-red-500/40 bg-red-950/20 p-4 text-center">
            <span className="text-3xl">🤡</span>
            <h3 className="mt-1 font-bold text-xs text-red-400">MANCO DE LA NOCHE</h3>
            <div className="my-2 flex items-center gap-2">
              <PlayerAvatar avatarAssetId={manco?.avatar_asset_id ?? null} color={manco?.color ?? null} role={manco?.role ?? 'player'} size="sm" />
              <span className="font-semibold text-sm" style={{ color: colorValue(manco?.color) }}>
                {manco?.nickname ?? 'Desconocido'}
              </span>
            </div>
            <p className="text-[10px] text-stone-400">Peores tiradas de dados registradas</p>
          </div>

          {/* Trofeo 3: El Traidor / La Muralla */}
          <div className="flex flex-col items-center rounded-xl border border-purple-500/40 bg-purple-950/20 p-4 text-center">
            <span className="text-3xl">🗡️</span>
            <h3 className="mt-1 font-bold text-xs text-purple-400">EL TRAIDOR DE LA GUERRA</h3>
            <div className="my-2 flex items-center gap-2">
              <PlayerAvatar avatarAssetId={traitor?.avatar_asset_id ?? null} color={traitor?.color ?? null} role={traitor?.role ?? 'player'} size="sm" />
              <span className="font-semibold text-sm" style={{ color: colorValue(traitor?.color) }}>
                {traitor?.nickname ?? 'Desconocido'}
              </span>
            </div>
            <p className="text-[10px] text-stone-400">Mayor cantidad de pactos rotos</p>
          </div>
        </div>

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
