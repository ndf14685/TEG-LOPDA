import { assetRegistry } from '../../services/assets/AssetRegistry';
import { colorValue } from '../../utils/playerColors';

const ROLE_EMOJI: Record<string, string> = {
  admin: '👑',
  player: '🪖',
  spectator: '👁️',
  ai_player: '🤖',
  ai_commentator: '🎙️',
};

export function PlayerAvatar({
  avatarAssetId,
  role,
  color,
  size = 'md',
}: {
  avatarAssetId: string | null;
  role: string;
  color: string | null;
  size?: 'sm' | 'md' | 'lg';
}) {
  const sizeClass = size === 'lg' ? 'w-16 h-16 text-4xl' : size === 'sm' ? 'w-7 h-7 text-base' : 'w-10 h-10 text-2xl';
  return (
    <span
      role="img"
      aria-label={`avatar de rol ${role}`}
      className={`${sizeClass} inline-flex items-center justify-center overflow-hidden rounded-full bg-war-800 border-2 shrink-0`}
      style={{ borderColor: colorValue(color) }}
    >
      {avatarAssetId ? (
        <img
          src={assetRegistry.urlForPath(avatarAssetId)}
          alt=""
          className="h-full w-full object-cover"
          onError={(e) => {
            // asset ausente: caer al emoji sin romper la UI
            (e.currentTarget.parentElement as HTMLElement).textContent = ROLE_EMOJI[role] ?? '🪖';
          }}
        />
      ) : (
        ROLE_EMOJI[role] ?? '🪖'
      )}
    </span>
  );
}
