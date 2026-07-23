import { create } from 'zustand';
import type { WsStatus } from '../services/websocket/wsClient';

interface ConnectionState {
  wsStatus: WsStatus;
  /** Mientras no esté 'synced', las acciones de juego quedan bloqueadas. */
  syncState: 'synced' | 'syncing' | 'lost';
  setWsStatus: (status: WsStatus) => void;
  setSyncState: (state: 'synced' | 'syncing' | 'lost') => void;
}

export const useConnectionStore = create<ConnectionState>((set) => ({
  wsStatus: 'idle',
  syncState: 'synced',
  setWsStatus: (wsStatus) => set({ wsStatus }),
  setSyncState: (syncState) => set({ syncState }),
}));
