import { z } from 'zod';

export const AssetKind = z.enum(['image', 'audio', 'video', 'emoji', 'json']);
export type AssetKind = z.infer<typeof AssetKind>;

export const AssetEntry = z.object({
  id: z.string(), // dot-notation: "background.lobby.war-room.001"
  kind: AssetKind,
  /** Ruta relativa a /assets para archivos, o el glifo para kind=emoji. */
  src: z.string(),
  preload: z.boolean().default(false),
  fallbackId: z.string().nullable().default(null),
});
export type AssetEntry = z.infer<typeof AssetEntry>;

export const AssetManifest = z.object({
  version: z.string(),
  assets: z.array(AssetEntry),
});
export type AssetManifest = z.infer<typeof AssetManifest>;
