import { create } from 'zustand';
import type { SessionResponse } from '@teg/contracts';

/**
 * Sesión activa. Se persiste en sessionStorage (no localStorage) para
 * sobrevivir refresh sin quedar permanente. Con backend real: cookie HttpOnly.
 */
interface SessionState {
  session: SessionResponse | null;
  adminToken: string | null; // sólo presente si este cliente creó la partida
  setSession: (session: SessionResponse) => void;
  setAdminToken: (token: string) => void;
  restore: (gameId: string) => boolean;
  clear: () => void;
}

const keyFor = (gameId: string) => `teg.session.${gameId}`;
const adminKeyFor = (gameId: string) => `teg.admin.${gameId}`;

export const useSessionStore = create<SessionState>((set, get) => ({
  session: null,
  adminToken: null,

  setSession: (session) => {
    sessionStorage.setItem(keyFor(session.gameId), JSON.stringify(session));
    set({ session });
  },

  setAdminToken: (token) => {
    const gameId = get().session?.gameId;
    if (gameId) sessionStorage.setItem(adminKeyFor(gameId), token);
    set({ adminToken: token });
  },

  restore: (gameId) => {
    try {
      const raw = sessionStorage.getItem(keyFor(gameId));
      if (!raw) return false;
      const session = JSON.parse(raw) as SessionResponse;
      const adminToken = sessionStorage.getItem(adminKeyFor(gameId));
      set({ session, adminToken });
      return true;
    } catch {
      return false;
    }
  },

  clear: () => set({ session: null, adminToken: null }),
}));
