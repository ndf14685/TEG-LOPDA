import type { SoundboardConfig } from '@teg/contracts';

/** Config del soundboard: los textos viven acá, nunca en los componentes. */
export const SOUNDBOARD_CONFIG: SoundboardConfig = {
  cooldownMs: 5000,
  buttons: [
    { id: 'soundboard.llora', label: 'Llorá', audioAssetId: null },
    { id: 'soundboard.que-robo', label: 'Qué robo', audioAssetId: null },
    { id: 'soundboard.toma', label: 'Tomá', audioAssetId: null },
    { id: 'soundboard.regalado', label: 'Regalado', audioAssetId: null },
    { id: 'soundboard.traidor', label: 'Traidor', audioAssetId: null },
    { id: 'soundboard.que-orto', label: 'Qué orto', audioAssetId: null },
    { id: 'soundboard.mira-esos-dados', label: 'Mirá esos dados', audioAssetId: null },
    { id: 'soundboard.te-regalaste', label: 'Te regalaste', audioAssetId: null },
    { id: 'soundboard.cine', label: 'Cine', audioAssetId: null },
    { id: 'soundboard.inteligencia-no-encontrada', label: 'Inteligencia no encontrada', audioAssetId: null },
  ],
};

export function soundboardLabel(id: string): string {
  return SOUNDBOARD_CONFIG.buttons.find((b) => b.id === id)?.label ?? id;
}
