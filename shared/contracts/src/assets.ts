import { z } from 'zod';

/**
 * Manifiestos publicados por Dirección de Arte en assets/manifest/
 * (ver assets/README-INTEGRATION.md).
 */

/** assets-manifest.json: mapas por modo de juego + piezas de UI. */
export const ArtAssetsManifest = z.object({
  schema_version: z.string(),
  maps: z.record(z.string(), z.object({ id: z.string(), path: z.string() })),
  ui: z.record(z.string(), z.string()),
});
export type ArtAssetsManifest = z.infer<typeof ArtAssetsManifest>;

/** audio-manifest.json: categorías → { nombre → {path, type} }. */
export const AudioManifest = z.object({
  schema_version: z.string(),
}).catchall(z.record(z.string(), z.object({ path: z.string(), type: z.string() })));
export type AudioManifest = z.infer<typeof AudioManifest>;

/** taunts-manifest.json: bardos con texto y sonido opcional, sobre un stamp visual. */
export const TauntsManifest = z.object({
  schema_version: z.string(),
  base_stamp_path: z.string(),
  definitions: z.array(z.object({
    id: z.string(),
    text: z.string(),
    sound: z.string().nullable(),
  })),
});
export type TauntsManifest = z.infer<typeof TauntsManifest>;

export const GameMode = z.enum(['classic_26', 'classic_50', 'mega_world_100']);
export type GameMode = z.infer<typeof GameMode>;

/** brand/palette/palette.json: tema global + colores de jugador (WCAG AA sobre fondo oscuro). */
export const BrandPalette = z.object({
  theme: z.string(),
  global: z.record(z.string(), z.string()),
  players: z.array(z.object({ id: z.string(), name: z.string(), hex: z.string() })),
});
export type BrandPalette = z.infer<typeof BrandPalette>;
