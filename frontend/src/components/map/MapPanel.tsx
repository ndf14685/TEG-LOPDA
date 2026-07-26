import { useEffect, useRef, useState } from 'react';
import type { GameMode } from '@teg/contracts';
import { assetRegistry } from '../../services/assets/AssetRegistry';
import { useGameStore } from '../../state/gameStore';
import { colorValue } from '../../utils/playerColors';
import { wsClient } from '../../services/websocket/wsClient';
import { FloatingEmotes } from '../chat/FloatingEmotes';
import { RadialMenu } from './RadialMenu';
import { territoryName } from '../../utils/territoryName';

const RUNTIME_STYLE = `
  /* los badges demo horneados en exports se ocultan: el juego dibuja los reales */
  .badge-group { display: none; }
  /* con base geográfica: la propiedad se lee por stroke/halo del color del
     dueño + tintado suave, para que costas y continentes sigan visibles.
     (las reglas de estado van DESPUÉS y ganan el empate de especificidad) */
  svg[data-geo-base] .territory.owned {
    stroke: var(--owner-color);
    stroke-width: 5;
    filter: drop-shadow(0 0 6px var(--owner-color));
  }
  .territory.hb-hover { stroke: #38bdf8; filter: brightness(1.25); }
  svg.hide-labels .territory-label, svg.hide-labels .continent-title { display: none; }
  .territory.attackable { stroke: #22d3ee; stroke-width: 6; stroke-dasharray: 6 6; }
  .territory.can-attack { stroke: #f59e0b; stroke-width: 5; stroke-dasharray: 10 6; cursor: crosshair; }
  .territory.frontier { stroke: #fbbf24; stroke-width: 4; stroke-dasharray: 4 8; }
  @keyframes teg-conquest-flash {
    0% { fill-opacity: 1; stroke: #fbbf24; stroke-width: 14; }
    50% { fill-opacity: 0.4; stroke: #fde68a; stroke-width: 8; }
    100% { fill-opacity: 0.75; stroke-width: 2; }
  }
  .territory.conquest-flash { animation: teg-conquest-flash 1.1s ease-out; }
  @keyframes teg-badge-pop {
    0% { transform: scale(0.4); opacity: 0; }
    70% { transform: scale(1.15); opacity: 1; }
    100% { transform: scale(1); opacity: 1; }
  }
  #tactical-overlay .army-badge { transform-box: fill-box; transform-origin: center; animation: teg-badge-pop 0.25s ease-out; }
`;

export function MapPanel({ mode }: { mode?: GameMode }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [state, setState] = useState<'loading' | 'ready' | 'missing'>('loading');

  const gameMode = useGameStore((s) => s.game?.game_mode);
  const effectiveMode = (mode ?? gameMode ?? 'classic_26') as GameMode;
  const turn = useGameStore((s) => s.turn);
  const stage = useGameStore((s) => s.stage);
  const placementRemaining = useGameStore((s) => s.placementRemaining);
  const placementPending = useGameStore((s) => s.placementPending);
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

            // El mapa CANÓNICO trae base + territorios + hitboxes + overlays en
            // un solo sistema, con su viewBox y capa geográfica ya correctos.
            // Se integra tal cual: sin inyectar base, sin expandir viewBox y sin
            // offsets. Solo se marca data-geo-base para el tintado suave que deja
            // ver las costas (la propiedad se sostiene con el halo del dueño).
            const isCanonical = (svg.getAttribute('id') ?? '').includes('canonical');
            if (isCanonical) {
              svg.setAttribute('data-geo-base', '1');
            } else {
              // --- ruta LEGACY (exports fragmentados táctico + geo_base) ---
              // saneo de clases de dueño demo (p-*): la propiedad la pinta el juego
              svg.querySelectorAll('.territory').forEach((t) => {
                Array.from(t.classList)
                  .filter((c) => c.startsWith('p-'))
                  .forEach((c) => t.classList.remove(c));
              });
              // base geográfica no interactiva debajo de la capa jugable
              const geoDigits = effectiveMode.replace(/\D/g, '');
              const geoBaseUrl = geoDigits && effectiveMode !== 'classic_26'
                ? assetRegistry.mapUrl(`geo_base_${geoDigits}` as GameMode)
                : null;
              if (geoBaseUrl) {
                try {
                  const baseRes = await fetch(geoBaseUrl);
                  if (baseRes.ok) {
                    const baseText = await baseRes.text();
                    const doc = new DOMParser().parseFromString(baseText, 'image/svg+xml');
                    const baseRoot = doc.documentElement;
                    if (baseRoot && baseRoot.tagName.toLowerCase() === 'svg' && !cancelled) {
                      svg.querySelector('#layer-1-geo-base')?.setAttribute('display', 'none');
                      const imported: Node[] = [];
                      Array.from(baseRoot.children).forEach((child) => {
                        const node = document.importNode(child, true);
                        if (node instanceof Element && node.id === 'layer-1-geo-base') {
                          node.setAttribute('id', 'layer-0-geo-world');
                        }
                        if (node instanceof Element && node.tagName.toLowerCase() !== 'defs') {
                          node.setAttribute('pointer-events', 'none');
                        }
                        imported.push(node);
                      });
                      imported.reverse().forEach((n) => svg.insertBefore(n, svg.firstChild));
                      svg.setAttribute('data-geo-base', '1');
                    }
                  }
                } catch {
                  // sin base: el mapa táctico funciona igual (fallback aprobado)
                }
              }
              // viewBox ajustado al contenido de exports que exceden su lienzo
              try {
                const bb = (svg as unknown as SVGGraphicsElement).getBBox();
                const vb = (svg.getAttribute('viewBox') ?? '0 0 2560 1440').split(' ').map(Number);
                const MARGIN = 80;
                const needW = Math.max(vb[2], bb.x + bb.width + MARGIN / 2);
                const needH = Math.max(vb[3], bb.y + bb.height + MARGIN);
                if (needW > vb[2] || needH > vb[3]) {
                  svg.setAttribute('viewBox', `0 0 ${Math.ceil(needW)} ${Math.ceil(needH)}`);
                  svg.querySelectorAll<SVGRectElement>('#layer-0-geo-world rect').forEach((r) => {
                    if (Number(r.getAttribute('width')) >= vb[2] - 1) {
                      r.setAttribute('width', String(Math.ceil(needW)));
                      r.setAttribute('height', String(Math.ceil(needH)));
                    }
                  });
                }
              } catch {
                // getBBox falla si el nodo no está montado: se conserva el viewBox
              }
            }
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
      path.dataset.mine = String(tState?.owner_player_id === youId);

      // 1. Pintar territorio según dueño. Con base geográfica el tintado es
      // suave (0.34) para que las costas se vean; la propiedad se sostiene con
      // el stroke/halo del color del dueño (clase .owned + --owner-color).
      const hasGeoBase = svg.hasAttribute('data-geo-base');
      path.classList.remove('owned');
      if (tState && tState.owner_player_id) {
        path.style.fill = ownerColorHex;
        path.style.fillOpacity = hasGeoBase ? '0.34' : '0.75';
        if (hasGeoBase) {
          path.classList.add('owned');
          path.style.setProperty('--owner-color', ownerColorHex);
        }
      } else {
        path.style.fill = 'rgba(30, 35, 45, 0.85)';
        path.style.fillOpacity = hasGeoBase ? '0.35' : '0.85';
      }

      // 2. Estado de Selección + vecinos atacables del origen elegido
      const myTurn = turn && turn.order[turn.index] === youId;
      const isFrontier = (mapAdjacency[id] ?? []).some(
        (n) => territories[n]?.owner_player_id !== youId,
      );
      path.classList.remove('selected', 'attack-source', 'attack-target', 'attackable', 'can-attack', 'frontier');
      // frontera propia: dónde conviene colocar (refuerzos y colocación inicial)
      const placing =
        (stage === 'placement_1' || stage === 'placement_2') ||
        (myTurn && stage === 'turns' && turn?.phase === 'reinforcement');
      if (placing && tState?.owner_player_id === youId && isFrontier && !selectedSource) {
        path.classList.add('frontier');
      }
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
      } else if (
        selectedSource &&
        turn?.phase === 'fortify' &&
        (mapAdjacency[selectedSource] ?? []).includes(id) &&
        tState &&
        tState.owner_player_id === youId
      ) {
        // destinos válidos del reagrupamiento
        path.classList.add('attackable');
      } else if (
        !selectedSource &&
        myTurn &&
        stage === 'turns' &&
        turn?.phase === 'attack' &&
        tState &&
        tState.owner_player_id === youId &&
        tState.armies > 1 &&
        (mapAdjacency[id] ?? []).some((n) => territories[n]?.owner_player_id !== youId)
      ) {
        // desde acá PODÉS atacar: el mapa te lo muestra solo
        path.classList.add('can-attack');
      }

      // 3. Tooltip nativo: nombre, dueño y tropas de un vistazo
      const ownerName = owner?.nickname ?? 'neutral';
      const prettyName = territoryName(id);
      let titleEl = path.querySelector<SVGTitleElement>('title');
      if (titleEl === null) {
        titleEl = document.createElementNS('http://www.w3.org/2000/svg', 'title');
        path.appendChild(titleEl);
      }
      titleEl.textContent = `${prettyName} — ${ownerName} (${tState?.armies ?? 0} tropas)`;

      // 4. Interacción directa: menú radial en territorios propios, puntería
      //    directa cuando ya hay un origen elegido. La capa de hitboxes
      //    (piloto Sudamérica) reusa este mismo handler más abajo.
      path.onclick = (e) => {
        e.stopPropagation();
        const state = useGameStore.getState();
        const container = containerRef.current;
        const rect = container?.getBoundingClientRect();
        const menuPos = rect
          ? { x: e.clientX - rect.left, y: e.clientY - rect.top }
          : { x: e.clientX, y: e.clientY };
        const isMine = tState?.owner_player_id === youId;
        const currentPhase = turn?.phase ?? 'attack';
        const adjacentToSource = state.selectedSourceTerritory
          ? (mapAdjacency[state.selectedSourceTerritory] ?? []).includes(id)
          : false;

        // colocación / refuerzos: radial +1/+3/MAX sobre tu país
        if (stage === 'placement_1' || stage === 'placement_2') {
          if (isMine && placementRemaining > 0) {
            state.setRadialMenu({ territoryId: id, ...menuPos });
          }
          return;
        }
        if (currentPhase === 'reinforcement') {
          if (isMine) state.setRadialMenu({ territoryId: id, ...menuPos });
          return;
        }

        // puntería activa: el click sobre un destino válido EJECUTA
        if (state.targetingMode === 'attack' && state.selectedSourceTerritory) {
          if (id === state.selectedSourceTerritory) {
            state.setTargetingMode(null);
            setSelectedSource(null);
            return;
          }
          if (!isMine && adjacentToSource) {
            setSelectedTarget(id);
            wsClient.send({
              type: 'attack',
              payload: {
                source_territory_id: state.selectedSourceTerritory,
                target_territory_id: id,
                attacker_dice: 3,
              },
            });
            return;
          }
          if (isMine) {
            // cambiar de origen sin salir del modo ataque
            state.setRadialMenu({ territoryId: id, ...menuPos });
            return;
          }
          return; // destino inválido: el resaltado ya explica cuáles valen
        }
        if (state.targetingMode === 'fortify' && state.selectedSourceTerritory) {
          if (id === state.selectedSourceTerritory) {
            state.setTargetingMode(null);
            setSelectedSource(null);
            return;
          }
          if (isMine && adjacentToSource) {
            setSelectedTarget(id);
            state.setFortifyPicker({ source: state.selectedSourceTerritory, target: id });
            state.setRadialMenu({ territoryId: id, ...menuPos });
            return;
          }
          return;
        }

        // sin puntería: tu país abre el radial; ajeno no hace nada acá
        if (isMine) {
          state.setRadialMenu({ territoryId: id, ...menuPos });
        } else {
          setSelectedSource(null);
          setSelectedTarget(null);
        }
      };

      // 4. Calcular centro para insignias de ejércitos (desplazadas hacia
      // abajo para no tapar el nombre del país)
      try {
        const bbox = path.getBBox();
        centers[id] = {
          x: bbox.x + bbox.width / 2,
          y: bbox.y + bbox.height / 2 + Math.min(bbox.height * 0.26, 62),
        };
      } catch {
        // Fallback si no está renderizado en screen
      }
    });

    // 4b. Capa de hitboxes separada (piloto Sudamérica): la interacción y el
    // tooltip viven en el hitbox transparente; el territorio visible solo pinta.
    svg.querySelectorAll<SVGPathElement>('.territory-hitbox').forEach((hb) => {
      const tid = hb.getAttribute('data-territory');
      if (!tid) return;
      const target = svg.querySelector<SVGPathElement>(`#${CSS.escape(tid)}`);
      if (!target) return;
      hb.onclick = target.onclick;
      hb.onmouseenter = () => target.classList.add('hb-hover');
      hb.onmouseleave = () => target.classList.remove('hb-hover');
      let hbTitle = hb.querySelector<SVGTitleElement>('title');
      if (hbTitle === null) {
        hbTitle = document.createElementNS('http://www.w3.org/2000/svg', 'title');
        hb.appendChild(hbTitle);
      }
      hbTitle.textContent = target.querySelector('title')?.textContent ?? '';
    });

    // 5. Inyectar Insignias de Ejércitos
    Object.entries(centers).forEach(([id, center]) => {
      const tState = territories[id];
      // durante la colocación, tus pendientes ocultos se te muestran a vos
      const pendingHere = placementPending[id] ?? 0;
      const armies = (tState ? tState.armies : 1) + pendingHere;
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
      circle.setAttribute('r', '34');
      circle.setAttribute('fill', '#0f172a');
      circle.setAttribute('fill-opacity', '0.92');
      circle.setAttribute('stroke', badgeColor);
      circle.setAttribute('stroke-width', id === selectedSource || id === selectedTarget ? '7' : '4');
      badgeGroup.appendChild(circle);

      // Texto con cantidad de ejércitos
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', String(center.x));
      text.setAttribute('y', String(center.y + 13));
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('fill', '#f8fafc');
      text.setAttribute('font-size', '36');
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
  }, [state, territories, players, youId, playerById, selectedSource, selectedTarget, setSelectedSource, setSelectedTarget, turn, mapAdjacency, stage, placementRemaining, placementPending]);

  // Flash de conquista: animación breve sobre el territorio recién tomado
  const conquestFlash = useGameStore((s) => s.conquestFlash);
  useEffect(() => {
    if (!conquestFlash || !containerRef.current) return;
    if (Date.now() - conquestFlash.ts > 2000) return;
    const path = containerRef.current.querySelector<SVGPathElement>(
      `#${CSS.escape(conquestFlash.territoryId)}`
    );
    if (!path) return;
    path.classList.remove('conquest-flash');
    // reinicia la animación aunque el mismo territorio caiga dos veces seguidas
    void path.getBoundingClientRect();
    path.classList.add('conquest-flash');
    const t = window.setTimeout(() => path.classList.remove('conquest-flash'), 1200);
    return () => window.clearTimeout(t);
  }, [conquestFlash]);

  // Zoom (rueda / pinch) y paneo (arrastre) manipulando el viewBox del SVG
  useEffect(() => {
    const container = containerRef.current;
    if (state !== 'ready' || !container) return;
    const svg = container.querySelector('svg');
    if (!svg) return;
    // el lienzo base sale del viewBox saneado en la carga (soporta exports
    // más altos que 1440 sin recortar el sur del mapa)
    if (!svg.getAttribute('viewBox')) svg.setAttribute('viewBox', '0 0 2560 1440');
    const [bx, by, bw, bh] = (svg.getAttribute('viewBox') ?? '0 0 2560 1440').split(' ').map(Number);
    const BASE = { x: bx, y: by, w: bw, h: bh };

    const view = () => {
      const [x, y, w, h] = (svg.getAttribute('viewBox') ?? '0 0 2560 1440').split(' ').map(Number);
      return { x, y, w, h };
    };
    const apply = (v: { x: number; y: number; w: number; h: number }) => {
      const w = Math.min(BASE.w, Math.max(BASE.w / 8, v.w));
      const h = (w / BASE.w) * BASE.h;
      const x = Math.min(BASE.w - w, Math.max(0, v.x));
      const y = Math.min(BASE.h - h, Math.max(0, v.y));
      svg.setAttribute('viewBox', `${x} ${y} ${w} ${h}`);
    };

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const v = view();
      const rect = container.getBoundingClientRect();
      const px = (e.clientX - rect.left) / rect.width;
      const py = (e.clientY - rect.top) / rect.height;
      const factor = e.deltaY > 0 ? 1.15 : 1 / 1.15;
      const w = v.w * factor;
      apply({ x: v.x + (v.w - w) * px, y: v.y + (v.h - w * (BASE.h / BASE.w)) * py, w, h: 0 });
    };

    // arrastre con umbral: un click corto sigue siendo click en el territorio
    const pointers = new Map<number, { x: number; y: number }>();
    let dragging = false;
    let pinchDist = 0;
    const onDown = (e: PointerEvent) => {
      pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (pointers.size === 2) {
        const [a, b] = [...pointers.values()];
        pinchDist = Math.hypot(a.x - b.x, a.y - b.y);
      }
    };
    const onMove = (e: PointerEvent) => {
      const prev = pointers.get(e.pointerId);
      if (!prev) return;
      const dx = e.clientX - prev.x;
      const dy = e.clientY - prev.y;
      if (pointers.size === 2) {
        pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
        const [a, b] = [...pointers.values()];
        const dist = Math.hypot(a.x - b.x, a.y - b.y);
        if (pinchDist > 0 && Math.abs(dist - pinchDist) > 2) {
          const v = view();
          apply({ ...v, w: v.w * (pinchDist / dist), h: 0 });
          pinchDist = dist;
        }
        return;
      }
      if (!dragging && Math.hypot(dx, dy) < 6) return;
      dragging = true;
      pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      const v = view();
      const rect = container.getBoundingClientRect();
      apply({ ...v, x: v.x - dx * (v.w / rect.width), y: v.y - dy * (v.h / rect.height) });
    };
    const onUp = (e: PointerEvent) => {
      pointers.delete(e.pointerId);
      if (dragging && pointers.size === 0) {
        dragging = false;
        // suprime el click fantasma post-arrastre
        const swallow = (ev: Event) => { ev.stopPropagation(); ev.preventDefault(); };
        container.addEventListener('click', swallow, { capture: true, once: true });
        window.setTimeout(() => container.removeEventListener('click', swallow, { capture: true }), 0);
      }
    };
    const onDblClick = () => apply({ ...BASE });

    container.addEventListener('wheel', onWheel, { passive: false });
    container.addEventListener('pointerdown', onDown);
    container.addEventListener('pointermove', onMove);
    container.addEventListener('pointerup', onUp);
    container.addEventListener('pointercancel', onUp);
    container.addEventListener('dblclick', onDblClick);
    return () => {
      container.removeEventListener('wheel', onWheel);
      container.removeEventListener('pointerdown', onDown);
      container.removeEventListener('pointermove', onMove);
      container.removeEventListener('pointerup', onUp);
      container.removeEventListener('pointercancel', onUp);
      container.removeEventListener('dblclick', onDblClick);
    };
  }, [state]);

  return (
    <div
      className="relative h-full w-full select-none overflow-hidden rounded-xl bg-war-950/90"
      data-testid="map-panel"
      onClick={() => {
        const s = useGameStore.getState();
        s.setRadialMenu(null);
        s.setFortifyPicker(null);
        s.setTargetingMode(null);
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

      {/* Toggle de etiquetas: valida reconocibilidad del mapa sin nombres */}
      {state === 'ready' && (
        <button
          data-testid="labels-toggle"
          onClick={(e) => {
            e.stopPropagation();
            containerRef.current?.querySelector('svg')?.classList.toggle('hide-labels');
          }}
          className="absolute left-3 top-3 z-20 rounded-lg border border-war-600 bg-war-900/90 px-2 py-1 text-xs font-bold text-stone-300 backdrop-blur-sm hover:border-gold-500"
          title="Mostrar/ocultar nombres de países"
        >
          Aa
        </button>
      )}

      {/* Menú radial táctico (posicionado relativo a este contenedor) */}
      {state === 'ready' && <RadialMenu />}

      {/* Leyenda Táctica del Mapa */}
      {state === 'ready' && (
        <div className="pointer-events-none absolute bottom-3 left-3 z-10 flex flex-wrap items-center gap-2 rounded-lg border border-war-700 bg-war-900/80 px-3 py-1.5 backdrop-blur-md">
          <span className="text-xs font-semibold text-stone-300">
            {turn?.phase === 'reinforcement'
              ? 'Tocá tus países: el menú radial coloca +1, +3 o el máximo'
              : turn?.phase === 'fortify'
                ? selectedSource
                  ? 'Tocá el país resaltado que recibe las tropas'
                  : 'Tocá un país tuyo y elegí FORTIFICAR'
                : selectedSource
                  ? 'Tocá el país enemigo resaltado: el combate arranca ahí mismo'
                  : 'Tocá un país tuyo (borde dorado) y elegí ATACAR'}
          </span>
        </div>
      )}
    </div>
  );
}
