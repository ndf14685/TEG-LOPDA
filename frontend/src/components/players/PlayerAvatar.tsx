import { assetRegistry } from '../../services/assets/AssetRegistry';
import { PLAYER_COLOR_VAR } from '../../utils/playerColors';
import type { PlayerColor } from '@teg/contracts';

export function PlayerAvatar({ avatarId, color, size = 'md' }: { avatarId: string; color: PlayerColor; size?: 'sm' | 'md' | 'lg' }) {
  const glyph = assetRegistry.emoji(avatarId);
  const sizeClass = size === 'lg' ? 'w-16 h-16 text-4xl' : size === 'sm' ? 'w-7 h-7 text-base' : 'w-10 h-10 text-2xl';
  return (
    <span
      role="img"
      aria-label={`avatar ${glyph}`}
      className={`${sizeClass} inline-flex items-center justify-center rounded-full bg-war-800 border-2 shrink-0`}
      style={{ borderColor: PLAYER_COLOR_VAR[color] }}
    >
      {glyph}
    </span>
  );
}
