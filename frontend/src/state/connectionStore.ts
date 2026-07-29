import { create } from 'zustand';
import type { WsStatus } from '../services/websocket/wsClient';

interface ConnectionState {
  wsStatus: WsStatus;
  /** Close code del cierre fatal (4009 = desalojado por otra pestaña/dispositivo). */
  revokedCode: number | null;
  /** Mientras no esté 'synced', las acciones de juego quedan bloqueadas. */
  syncState: 'synced' | 'syncing' | 'lost';
  setWsStatus: (status: WsStatus, closeCode?: number) => void;
  setSyncState: (state: 'synced' | 'syncing' | 'lost') => void;
}

export const useConnectionStore = create<ConnectionState>((set) => ({
  wsStatus: 'idle',
  revokedCode: null,
  syncState: 'synced',
  setWsStatus: (wsStatus, closeCode) => set({ wsStatus, revokedCode: wsStatus === 'revoked' ? (closeCode ?? null) : null }),
  setSyncState: (syncState) => set({ syncState }),
}));
