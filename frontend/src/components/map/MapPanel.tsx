import { useEffect, useRef, useState } from 'react';
import type { GameMode } from '@teg/contracts';
import { assetRegistry } from '../../services/assets/AssetRegistry';

/**
 * Mapa táctico: inyecta el SVG de Dirección de Arte (assets/maps/base/…)
 * directamente en el DOM, como pide assets/README-INTEGRATION.md — nunca
 * una imagen plana. Los territorios se pintarán vía path.style.fill cuando
 * el backend publique estado de territorios (TODO teg-rules).
 */
export function MapPanel({ mode = 'classic_50' }: { mode?: GameMode }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [state, setState] = useState<'loading' | 'ready' | 'missing'>('loading');

  useEffect(() => {
    let cancelled = false;
    const url = assetRegistry.mapUrl(mode);
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
          // SVG de la propia app (Dirección de Arte), no contenido de usuario
          containerRef.current.innerHTML = text;
          const svg = containerRef.current.querySelector('svg');
          svg?.setAttribute('width', '100%');
          svg?.setAttribute('height', '100%');
          svg?.setAttribute('role', 'group');
          svg?.setAttribute('aria-label', 'Mapa del juego');
        }
        setState('ready');
      })
      .catch(() => {
        if (!cancelled) setState('missing');
      });
    return () => { cancelled = true; };
  }, [mode]);

  return (
    <div className="relative h-full w-full" data-testid="map-panel">
      <div ref={containerRef} className={`h-full w-full ${state === 'ready' ? '' : 'hidden'}`} />
      {state !== 'ready' && (
        <div className="flex h-full min-h-64 flex-col items-center justify-center gap-3 text-center">
          <span className="text-6xl" aria-hidden>🗺️</span>
          {state === 'loading' ? (
            <p className="text-sm text-stone-400">Desplegando el mapa táctico…</p>
          ) : (
            <>
              <p className="text-sm text-stone-400">El mapa está en producción en Dirección de Arte.</p>
              <p className="max-w-sm text-xs text-stone-600">
                Cuando <code>assets/maps/base/</code> tenga las mallas SVG, este panel las inyecta
                solo. Mientras tanto: dados, ataques y bardeo funcionan igual.
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
