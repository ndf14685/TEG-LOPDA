import { z } from 'zod';

export const TerritoryState = z.object({
  id: z.string(), // id estable, dot-notation: "america-sur.argentina"
  continent: z.string(),
  ownerId: z.string().nullable(),
  armies: z.number().int().min(0),
});
export type TerritoryState = z.infer<typeof TerritoryState>;

/** Topología estática del mapa del slice (2 continentes, 8 territorios). */
export interface TerritoryDef {
  id: string;
  name: string;
  continent: string;
  borders: string[];
}

export const SLICE_MAP: TerritoryDef[] = [
  { id: 'america-sur.argentina', name: 'Argentina', continent: 'america-sur', borders: ['america-sur.chile', 'america-sur.brasil', 'america-sur.uruguay'] },
  { id: 'america-sur.chile', name: 'Chile', continent: 'america-sur', borders: ['america-sur.argentina', 'america-sur.brasil'] },
  { id: 'america-sur.brasil', name: 'Brasil', continent: 'america-sur', borders: ['america-sur.argentina', 'america-sur.chile', 'america-sur.uruguay', 'africa.sahara'] },
  { id: 'america-sur.uruguay', name: 'Uruguay', continent: 'america-sur', borders: ['america-sur.argentina', 'america-sur.brasil'] },
  { id: 'africa.sahara', name: 'Sahara', continent: 'africa', borders: ['america-sur.brasil', 'africa.egipto', 'africa.sudafrica'] },
  { id: 'africa.egipto', name: 'Egipto', continent: 'africa', borders: ['africa.sahara', 'africa.madagascar'] },
  { id: 'africa.sudafrica', name: 'Sudáfrica', continent: 'africa', borders: ['africa.sahara', 'africa.madagascar'] },
  { id: 'africa.madagascar', name: 'Madagascar', continent: 'africa', borders: ['africa.egipto', 'africa.sudafrica'] },
];
