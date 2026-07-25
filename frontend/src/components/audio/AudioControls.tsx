import { useGameStore } from '../../state/gameStore';
import { audioService } from '../../services/audio/AudioService';

/** Toggle global de sonidos del juego (dados, combate, reacciones, bardeo).
 * Silenciados por default; el que los quiera oír los activa acá. */
export function AudioControls() {
  const soundsMuted = useGameStore((s) => s.soundsMuted);
  const setSoundsMuted = useGameStore((s) => s.setSoundsMuted);

  function toggle() {
    const next = !soundsMuted;
    setSoundsMuted(next);
    audioService.unlock();
    for (const ch of ['music', 'sfx', 'taunts'] as const) audioService.setMuted(ch, next);
  }

  return (
    <button
      onClick={toggle}
      data-testid="sounds-toggle"
      aria-pressed={!soundsMuted}
      className="flex items-center justify-center gap-2 rounded-lg border border-war-700 bg-war-900 px-3 py-1.5 text-xs text-stone-400 hover:border-gold-500 hover:text-stone-200"
    >
      {soundsMuted ? 'Sonidos: OFF' : 'Sonidos: ON'}
    </button>
  );
}
