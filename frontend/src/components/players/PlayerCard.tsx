import type { PlayerPublic } from '@teg/contracts';
import { PlayerAvatar } from './PlayerAvatar';
import { PLAYER_COLOR_VAR } from '../../utils/playerColors';

const ROLE_LABEL: Record<PlayerPublic['role'], string> = {
  admin: 'ADMIN',
  player: '',
  spectator: 'ESPECTADOR',
  'ai-player': 'IA',
};

export function PlayerCard({ player, isSelf }: { player: PlayerPublic; isSelf?: boolean }) {
  const connected = player.connection === 'connected';
  return (
    <li
      data-testid={`player-card-${player.nickname}`}
      className={`flex items-center gap-3 rounded-lg px-3 py-2 bg-war-800/80 border border-war-700 ${connected ? '' : 'opacity-50'}`}
    >
      <PlayerAvatar avatarId={player.avatarId} color={player.color} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate font-semibold" style={{ color: PLAYER_COLOR_VAR[player.color] }}>
            {player.nickname}
          </span>
          {isSelf && <span className="text-xs text-stone-400">(vos)</span>}
          {ROLE_LABEL[player.role] && (
            <span className="rounded bg-war-700 px-1.5 py-0.5 text-[10px] tracking-wider text-gold-400">{ROLE_LABEL[player.role]}</span>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-stone-400">
          <span aria-hidden className={`inline-block h-2 w-2 rounded-full ${connected ? 'bg-green-500' : 'bg-stone-600'}`} />
          <span>{connected ? 'conectado' : player.connection === 'disconnected' ? 'desconectado' : 'sin entrar'}</span>
          {player.titles.length > 0 && <span className="truncate text-gold-500">🏅 {player.titles[0]}</span>}
        </div>
      </div>
      <span
        data-testid={`ready-${player.nickname}`}
        className={`text-lg ${player.ready ? '' : 'grayscale opacity-30'}`}
        title={player.ready ? 'Listo' : 'No listo'}
        aria-label={player.ready ? `${player.nickname} listo` : `${player.nickname} no listo`}
      >
        ✅
      </span>
    </li>
  );
}
