import { useEffect, useRef, useState } from 'react';
import type { GameMode } from '@teg/contracts';
import { assetRegistry } from '../../services/assets/AssetRegistry';
import { useGameStore } from '../../state/gameStore';
import { colorValue } from '../../utils/playerColors';
import { wsClient } from '../../services/websocket/wsClient';
import { FloatingEmotes } from '../chat/FloatingEmotes';

const RUNTIME_STYLE = `
  .territory.attackable { stroke: #22d3ee; stroke-width: 6; stroke-dasharray: 6 6; }
`;

export function MapPanel({ mode }: { mode?: GameMode }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [state, setState] = useState<'loading' | 'ready' | 'missing'>('loading');

  const gameMode = useGameStore((s) => s.game?.game_mode);
  const effectiveMode = (mode ?? gameMode ?? 'classic_26') as GameMode;
  const turn = useGameStore((s) => s.turn);
  const mapAdjacency = useGameStore((s) => s.mapAdjacency);
  const territories = useGameStore((s) => s.territories);
  const players = useGameStore((s) => s.players);
  const youId = useGameStore((s) => s.youId);
  const playerById = useGameStore((s) => s.playerById);
  const selectedSource = useGameStore((s) => s.selectedSourceTerritory);
  const selectedTarget = useGameStore((s) => s.selectedTargetTerritory);
  const setSelectedSource = useGameStore((s) => s.setSelectedSourceTerritory);
  const setSelectedTarget = useGameStore((s) => s.setSelectedTargetTerritory);

  // Carga del SVG en el DOM
  useEffect(() => {
    let cancelled = false;
    const url = assetRegistry.mapUrl(effectiveMode);
    if (!url) {
      setState('missing');
      return;
    }
    fetch(url)
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const text = await res.text();
        if (cancelled) return;
        if (!text.trimStart().startsWith('<svg') && !text.includes('<svg')) throw new Error('no es un SVG');
        if (containerRef.current) {
          containerRef.current.innerHTML = text;
          const svg = containerRef.current.querySelector('svg');
          if (svg) {
            svg.setAttribute('width', '100%');
            svg.setAttribute('height', '100%');
            svg.setAttribute('role', 'group');
            svg.setAttribute('aria-label', 'Mapa del juego');
            // estilos de runtime (p. ej. .attackable) para cualquier malla
            const style = document.createElementNS('http://www.w3.org/2000/svg', 'style');
            style.textContent = RUNTIME_STYLE;
            svg.appendChild(style);
          }
        }
        setState('ready');
      })
      .catch(() => {
        if (!cancelled) setState('missing');
      });
    return () => {
      cancelled = true;
    };
  }, [effectiveMode]);

  // Actualización táctica: Colores, click listeners, medallas de ejércitos y línea de ataque
  useEffect(() => {
    if (state !== 'ready' || !containerRef.current) return;
    const svg = containerRef.current.querySelector('svg');
    if (!svg) return;

    const pathElements = Array.from(svg.querySelectorAll<SVGPathElement>('.territory'));

    // Limpiar overlays anteriores
    let overlayGroup = svg.querySelector<SVGGElement>('#tactical-overlay');
    if (!overlayGroup) {
      overlayGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      overlayGroup.setAttribute('id', 'tactical-overlay');
      svg.appendChild(overlayGroup);
    }
    overlayGroup.innerHTML = '';

    const centers: Record<string, { x: number; y: number }> = {};

    pathElements.forEach((path) => {
      const id = path.getAttribute('id');
      if (!id) return;

      const tState = territories[id];
      const owner = tState ? playerById(tState.owner_player_id) : undefined;
      const ownerColorHex = owner ? colorValue(owner.color) : 'rgba(30, 35, 45, 0.85)';

      // 1. Pintar territorio según dueño
      if (tState && tState.owner_player_id) {
        path.style.fill = ownerColorHex;
        path.style.fillOpacity = '0.75';
      } else {
        path.style.fill = 'rgba(30, 35, 45, 0.85)';
        path.style.fillOpacity = '0.85';
      }

      // 2. Estado de Selección + vecinos atacables del origen elegido
      path.classList.remove('selected', 'attack-source', 'attack-target', 'attackable');
      if (id === selectedSource) {
        path.classList.add('attack-source', 'selected');
      } else if (id === selectedTarget) {
        path.classList.add('attack-target');
      } else if (
        selectedSource &&
        turn?.phase === 'attack' &&
        (mapAdjacency[selectedSource] ?? []).includes(id) &&
        tState &&
        tState.owner_player_id !== youId
      ) {
        path.classList.add('attackable');
      }

      // 3. Event Listener para interacción según Fase del Turno
      path.onclick = (e) => {
        e.stopPropagation();
        const currentPhase = turn?.phase ?? 'attack';

        if (currentPhase === 'reinforcement') {
          if (tState && tState.owner_player_id === youId) {
            wsClient.send({
              type: 'turn.place_reinforcement',
              payload: { territory_id: id, count: 1 },
            });
          }
          return;
        }

        if (id === selectedSource) {
          setSelectedSource(null);
          setSelectedTarget(null);
          return;
        }
        if (tState && tState.owner_player_id === youId) {
          // en reagrupamiento, un segundo territorio propio es el destino
          if (currentPhase === 'fortify' && selectedSource) {
            setSelectedTarget(id);
          } else {
            setSelectedSource(id);
            if (selectedTarget === id) setSelectedTarget(null);
          }
        } else if (selectedSource && selectedSource !== id) {
          setSelectedTarget(id);
        }
      };

      // 4. Calcular centro para insignias de ejércitos (desplazadas hacia
      // abajo para no tapar el nombre del país)
      try {
        const bbox = path.getBBox();
        centers[id] = {
          x: bbox.x + bbox.width / 2,
          y: bbox.y + bbox.height / 2 + Math.min(bbox.height * 0.18, 42),
        };
      } catch {
        // Fallback si no está renderizado en screen
      }
    });

    // 5. Inyectar Insignias de Ejércitos
    Object.entries(centers).forEach(([id, center]) => {
      const tState = territories[id];
      const armies = tState ? tState.armies : 1;
      const owner = tState ? playerById(tState.owner_player_id) : undefined;
      const badgeColor = owner ? colorValue(owner.color) : '#94a3b8';

      const badgeGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      badgeGroup.setAttribute('class', 'army-badge');
      badgeGroup.setAttribute('pointer-events', 'none');

      // Círculo de fondo — el viewBox es 2560x1440, en pantalla se reduce
      // ~4x: la insignia debe ser grande para que las tropas se lean
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', String(center.x));
      circle.setAttribute('cy', String(center.y));
      circle.setAttribute('r', '44');
      circle.setAttribute('fill', '#0f172a');
      circle.setAttribute('fill-opacity', '0.92');
      circle.setAttribute('stroke', badgeColor);
      circle.setAttribute('stroke-width', id === selectedSource || id === selectedTarget ? '9' : '5');
      badgeGroup.appendChild(circle);

      // Texto con cantidad de ejércitos
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', String(center.x));
      text.setAttribute('y', String(center.y + 16));
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('fill', '#f8fafc');
      text.setAttribute('font-size', '46');
      text.setAttribute('font-weight', '900');
      text.setAttribute('font-family', 'sans-serif');
      text.textContent = String(armies);
      badgeGroup.appendChild(text);

      overlayGroup?.appendChild(badgeGroup);
    });

    // 6. Flecha/Línea Táctica entre Origen y Destino si ambos están seleccionados
    if (selectedSource && selectedTarget && centers[selectedSource] && centers[selectedTarget]) {
      const srcCenter = centers[selectedSource];
      const tgtCenter = centers[selectedTarget];

      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', String(srcCenter.x));
      line.setAttribute('y1', String(srcCenter.y));
      line.setAttribute('x2', String(tgtCenter.x));
      line.setAttribute('y2', String(tgtCenter.y));
      line.setAttribute('stroke', '#ef4444');
      line.setAttribute('stroke-width', '10');
      line.setAttribute('stroke-dasharray', '18 10');
      line.setAttribute('pointer-events', 'none');
      overlayGroup.appendChild(line);
    }
  }, [state, territories, players, youId, playerById, selectedSource, selectedTarget, setSelectedSource, setSelectedTarget, turn, mapAdjacency]);

  return (
    <div
      className="relative h-full w-full select-none overflow-hidden rounded-xl bg-war-950/90"
      data-testid="map-panel"
      onClick={() => {
        setSelectedSource(null);
        setSelectedTarget(null);
      }}
    >
      <div ref={containerRef} className={`h-full w-full ${state === 'ready' ? '' : 'hidden'}`} />
      {state !== 'ready' && (
        <div className="flex h-full min-h-64 flex-col items-center justify-center gap-3 text-center">
          <span className="text-6xl" aria-hidden>
            🗺️
          </span>
          {state === 'loading' ? (
            <p className="text-sm text-stone-400">Desplegando el mapa táctico…</p>
          ) : (
            <>
              <p className="text-sm text-stone-400">Cargando la malla SVG táctica…</p>
            </>
          )}
        </div>
      )}

      {/* Reacciones Flotantes & Emotes sobre el mapa */}
      {state === 'ready' && <FloatingEmotes />}

      {/* Leyenda Táctica del Mapa */}
      {state === 'ready' && (
        <div className="pointer-events-none absolute bottom-3 left-3 z-10 flex flex-wrap items-center gap-2 rounded-lg border border-war-700 bg-war-900/80 px-3 py-1.5 backdrop-blur-md">
          <span className="text-xs font-semibold text-stone-300">
            {turn?.phase === 'reinforcement'
              ? '🪖 Tocá tus países para colocar refuerzos'
              : turn?.phase === 'fortify'
                ? selectedSource
                  ? '🛡️ Elegí otro país tuyo como destino'
                  : '🛡️ Elegí el país tuyo de origen'
                : selectedSource
                  ? selectedTarget
                    ? '⚔️ Listo para atacar (botón en el panel derecho)'
                    : '🎯 Seleccioná un país objetivo'
                  : '👉 Hacé click en tu país para atacar'}
          </span>
        </div>
      )}
    </div>
  );
}
