import { useConnectionStore } from '../state/connectionStore';

/** Close code 4009: el backend desalojó esta pestaña por exceso de conexiones simultáneas (tope de 3 por jugador). */
const EVICTED_CLOSE_CODE = 4009;

/** Indicador de reconexión/sincronización. El estado 'revoked' es terminal (kick, token regenerado o desalojo por otra pestaña/dispositivo). */
export function ConnectionBanner() {
  const wsStatus = useConnectionStore((s) => s.wsStatus);
  const revokedCode = useConnectionStore((s) => s.revokedCode);
  const syncState = useConnectionStore((s) => s.syncState);

  if (wsStatus === 'revoked') {
    const message = revokedCode === EVICTED_CLOSE_CODE
      ? '📱 Abriste el juego en otra pestaña o dispositivo. Esta sesión se cerró.'
      : '🚫 Tu acceso fue revocado por el administrador.';
    return (
      <div role="alert" className="fixed inset-x-0 top-0 z-50 bg-red-950 px-4 py-1.5 text-center text-sm font-medium text-red-100">
        {message}
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
