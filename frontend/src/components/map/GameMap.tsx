import { useMemo, useState } from 'react';
import { SLICE_MAP } from '@teg/contracts';
import { useGameStore } from '../../state/gameStore';
import { TERRITORY_SHAPES } from './territoryLayout';
import { PLAYER_COLOR_VAR } from '../../utils/playerColors';

const NAME_BY_ID = new Map(SLICE_MAP.map((t) => [t.id, t.name]));
const BORDERS_BY_ID = new Map(SLICE_MAP.map((t) => [t.id, new Set(t.borders)]));

/** Mapa SVG data-driven. Colores de dueño vía CSS variables, nunca hardcodeados en el SVG. */
export function GameMap() {
  const snapshot = useGameStore((s) => s.snapshot);
  const selectedId = useGameStore((s) => s.selectedTerritoryId);
  const selectTerritory = useGameStore((s) => s.selectTerritory);
  const playerById = useGameStore((s) => s.playerById);
  const [hoverId, setHoverId] = useState<string | null>(null);

  const stateById = useMemo(
    () => new Map((snapshot?.territories ?? []).map((t) => [t.id, t])),
    [snapshot?.territories],
  );

  const validBorders = selectedId ? BORDERS_BY_ID.get(selectedId) : null;
  const hovered = hoverId ? stateById.get(hoverId) : null;
  const hoveredOwner = hovered ? playerById(hovered.ownerId) : undefined;

  return (
    <div className="relative h-full w-full overflow-auto" data-testid="game-map">
      <svg viewBox="0 0 590 300" role="group" aria-label="Mapa del juego" className="h-full w-full min-h-64">
        {/* etiquetas de continente */}
        <text x="145" y="30" className="fill-stone-500 text-[13px] font-bold tracking-widest">AMÉRICA DEL SUR</text>
        <text x="400" y="30" className="fill-stone-500 text-[13px] font-bold tracking-widest">ÁFRICA</text>
        {/* puente entre continentes */}
        <line x1="230" y1="95" x2="335" y2="100" stroke="#3f3f46" strokeWidth="2" strokeDasharray="5 4" />

        {TERRITORY_SHAPES.map((shape) => {
          const state = stateById.get(shape.id);
          const owner = playerById(state?.ownerId);
          const classes = [
            'territory',
            selectedId === shape.id ? 'selected' : '',
            validBorders?.has(shape.id) ? 'attack-target' : '',
          ].filter(Boolean).join(' ');
          return (
            <g key={shape.id}>
              <polygon
                data-testid={`territory-${shape.id}`}
                className={classes}
                points={shape.points}
                style={{ ['--territory-color' as string]: owner ? PLAYER_COLOR_VAR[owner.color] : undefined }}
                tabIndex={0}
                role="button"
                aria-label={`${NAME_BY_ID.get(shape.id)}: ${owner ? `de ${owner.nickname}` : 'neutral'}, ${state?.armies ?? 0} ejércitos`}
                onClick={() => selectTerritory(selectedId === shape.id ? null : shape.id)}
                onKeyDown={(e) => e.key === 'Enter' && selectTerritory(selectedId === shape.id ? null : shape.id)}
                onMouseEnter={() => setHoverId(shape.id)}
                onMouseLeave={() => setHoverId(null)}
              />
              <text x={shape.labelX} y={shape.labelY} textAnchor="middle" className="pointer-events-none fill-stone-100 text-[11px] font-semibold" style={{ paintOrder: 'stroke', stroke: '#0a0f0a', strokeWidth: 2 }}>
                {NAME_BY_ID.get(shape.id)}
              </text>
              <text x={shape.labelX} y={shape.labelY + 16} textAnchor="middle" className="pointer-events-none fill-white text-[13px] font-bold" style={{ paintOrder: 'stroke', stroke: '#0a0f0a', strokeWidth: 2 }}>
                {state?.armies ?? ''}
              </text>
            </g>
          );
        })}
      </svg>

      {hovered && (
        <div className="pointer-events-none absolute bottom-2 left-2 rounded bg-war-900/95 px-3 py-1.5 text-xs shadow-lg border border-war-700">
          <strong>{NAME_BY_ID.get(hovered.id)}</strong>
          {' · '}{hoveredOwner ? hoveredOwner.nickname : 'neutral'}
          {' · '}{hovered.armies} ejércitos
        </div>
      )}
    </div>
  );
}
