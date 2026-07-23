import type { PublicPlayer } from '@teg/contracts';
import { PlayerAvatar } from './PlayerAvatar';
import { colorValue } from '../../utils/playerColors';

const ROLE_LABEL: Record<string, string> = {
  admin: 'ADMIN',
  player: '',
  spectator: 'ESPECTADOR',
  ai_player: 'IA',
  ai_commentator: 'RELATOR',
};

const PRESENCE_LABEL: Record<string, string> = {
  online: 'conectado',
  reconnecting: 'reconectando…',
  offline: 'desconectado',
};

export function PlayerCard({ player, isSelf }: { player: PublicPlayer; isSelf?: boolean }) {
  const presence = player.presence ?? (player.joined ? 'offline' : 'offline');
  const online = presence === 'online';
  const neverJoined = !player.joined;
  return (
    <li
      data-testid={`player-card-${player.nickname}`}
      className={`flex items-center gap-3 rounded-lg px-3 py-2 bg-war-800/80 border border-war-700 ${online ? '' : 'opacity-50'}`}
    >
      <PlayerAvatar avatarAssetId={player.avatar_asset_id} role={player.role} color={player.color} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate font-semibold" style={{ color: colorValue(player.color) }}>
            {player.nickname}
          </span>
          {isSelf && <span className="text-xs text-stone-400">(vos)</span>}
          {ROLE_LABEL[player.role] && (
            <span className="rounded bg-war-700 px-1.5 py-0.5 text-[10px] tracking-wider text-gold-400">{ROLE_LABEL[player.role]}</span>
          )}
          {player.eliminated && <span className="text-xs">💀</span>}
        </div>
        <div className="flex items-center gap-2 text-xs text-stone-400">
          <span
            aria-hidden
            className={`inline-block h-2 w-2 rounded-full ${online ? 'bg-green-500' : presence === 'reconnecting' ? 'bg-yellow-500 animate-pulse' : 'bg-stone-600'}`}
          />
          <span>{neverJoined ? 'sin entrar' : PRESENCE_LABEL[presence]}</span>
        </div>
      </div>
      <span
        data-testid={`ready-${player.nickname}`}
        className={`text-lg ${player.is_ready ? '' : 'grayscale opacity-30'}`}
        title={player.is_ready ? 'Listo' : 'No listo'}
        aria-label={player.is_ready ? `${player.nickname} listo` : `${player.nickname} no listo`}
      >
        ✅
      </span>
    </li>
  );
}
