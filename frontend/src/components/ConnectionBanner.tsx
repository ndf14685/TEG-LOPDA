import { useConnectionStore } from '../state/connectionStore';

/** Indicador de reconexión/sincronización. Bloquea visualmente cuando el estado no es confiable. */
export function ConnectionBanner() {
  const wsStatus = useConnectionStore((s) => s.wsStatus);
  const syncState = useConnectionStore((s) => s.syncState);

  if (wsStatus === 'open' && syncState === 'synced') return null;
  const reconnecting = wsStatus === 'reconnecting';
  return (
    <div
      role="status"
      className={`fixed inset-x-0 top-0 z-50 px-4 py-1.5 text-center text-sm font-medium ${reconnecting ? 'bg-red-900 text-red-100' : 'bg-yellow-900 text-yellow-100'}`}
    >
      {reconnecting ? '⚠️ Conexión perdida — reintentando…' : '⏳ Sincronizando estado…'}
    </div>
  );
}
