import { useConnectionStore } from '../state/connectionStore';

/** Indicador de reconexión/sincronización. El estado 'revoked' es terminal (kick o token regenerado). */
export function ConnectionBanner() {
  const wsStatus = useConnectionStore((s) => s.wsStatus);
  const syncState = useConnectionStore((s) => s.syncState);

  if (wsStatus === 'revoked') {
    return (
      <div role="alert" className="fixed inset-x-0 top-0 z-50 bg-red-950 px-4 py-1.5 text-center text-sm font-medium text-red-100">
        🚫 Tu acceso fue revocado por el administrador.
      </div>
    );
  }
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
