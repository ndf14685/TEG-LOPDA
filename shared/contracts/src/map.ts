import { z } from 'zod';

/**
 * Estado de territorio previsto para cuando el backend implemente el mapa
 * (TODO teg-rules). Los IDs deben ser los de las mallas SVG de Dirección de
 * Arte, ej: "territory-south-america-argentina".
 */
export const TerritoryState = z.object({
  id: z.string(),
  owner_player_id: z.string().nullable(),
  armies: z.number().int().min(0),
});
export type TerritoryState = z.infer<typeof TerritoryState>;
