import { z } from 'zod';

/**
 * Botón de bardeo rápido. La fuente canónica es assets/manifest/taunts-manifest.json
 * (Dirección de Arte); esta forma es la normalización que consume la UI.
 */
export const SoundboardButton = z.object({
  id: z.string(),
  label: z.string(),
  soundPath: z.string().nullable().default(null),
});
export type SoundboardButton = z.infer<typeof SoundboardButton>;
