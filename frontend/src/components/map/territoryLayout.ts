/** Geometría del mapa del slice. Separada del componente para poder crecer a un SVG real. */
export interface TerritoryShape {
  id: string;
  points: string; // polygon points
  labelX: number;
  labelY: number;
}

export const TERRITORY_SHAPES: TerritoryShape[] = [
  { id: 'america-sur.chile', points: '60,150 95,140 105,240 70,255', labelX: 84, labelY: 200 },
  { id: 'america-sur.argentina', points: '95,140 175,135 185,235 105,240', labelX: 140, labelY: 190 },
  { id: 'america-sur.brasil', points: '110,55 220,50 230,130 175,135 95,140', labelX: 165, labelY: 95 },
  { id: 'america-sur.uruguay', points: '175,135 230,130 235,175 185,175', labelX: 205, labelY: 155 },
  { id: 'africa.sahara', points: '330,60 440,55 445,140 335,145', labelX: 385, labelY: 100 },
  { id: 'africa.egipto', points: '440,55 530,65 525,145 445,140', labelX: 485, labelY: 105 },
  { id: 'africa.sudafrica', points: '335,145 445,140 440,235 345,230', labelX: 390, labelY: 190 },
  { id: 'africa.madagascar', points: '445,140 525,145 520,230 440,235', labelX: 482, labelY: 190 },
];
