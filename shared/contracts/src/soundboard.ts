import { z } from 'zod';

export const SoundboardButton = z.object({
  id: z.string(), // "soundboard.llora"
  label: z.string(),
  audioAssetId: z.string().nullable().default(null),
});
export type SoundboardButton = z.infer<typeof SoundboardButton>;

export const SoundboardConfig = z.object({
  cooldownMs: z.number().int().default(5000),
  buttons: z.array(SoundboardButton),
});
export type SoundboardConfig = z.infer<typeof SoundboardConfig>;
