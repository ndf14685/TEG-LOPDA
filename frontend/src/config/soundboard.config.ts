import type { SoundboardButton } from '@teg/contracts';

/**
 * Fallback del soundboard cuando assets/manifest/taunts-manifest.json aún no
 * está disponible. La fuente canónica es el manifest de Dirección de Arte
 * (assetRegistry.soundboardButtons(FALLBACK_SOUNDBOARD)).
 */
export const FALLBACK_SOUNDBOARD: SoundboardButton[] = [
  { id: 'bardo_llora', label: 'Llorá', soundPath: null },
  { id: 'bardo_que-robo', label: 'Qué robo', soundPath: null },
  { id: 'bardo_toma', label: 'Tomá', soundPath: null },
  { id: 'bardo_regalado', label: 'Regalado', soundPath: null },
  { id: 'bardo_traidor', label: 'Traidor', soundPath: null },
  { id: 'bardo_que-orto', label: 'Qué orto', soundPath: null },
  { id: 'bardo_mira-esos-dados', label: 'Mirá esos dados', soundPath: null },
  { id: 'bardo_te-regalaste', label: 'Te regalaste', soundPath: null },
  { id: 'bardo_cine', label: 'Cine', soundPath: null },
  { id: 'bardo_inteligencia-no-encontrada', label: 'Inteligencia no encontrada', soundPath: null },
];

export const SOUNDBOARD_COOLDOWN_MS = 5000;
