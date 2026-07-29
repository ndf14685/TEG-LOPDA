import { create } from 'zustand';

/**
 * Sesión de jugador por partida. El token de join es la credencial WS: se
 * guarda en sessionStorage (no localStorage) — pedido explícito al backend
 * de cookie HttpOnly queda para producción.
 */
export interface PlayerSession {
  code: string; // código público de la sala (va en URLs)
  gameId: string; // uuid interno (solo lo usa el admin)
  token: string;
  playerId: string;
  nickname: string;
  role: string;
}

interface SessionState {
  session: PlayerSession | null;
  /** X-Admin-Token global del servidor; solo presente en el navegador del admin. */
  adminToken: string | null;
  setSession: (session: PlayerSession) => void;
  setAdminToken: (token: string) => void;
  restore: (code: string) => boolean;
  clear: () => void;
}

const keyFor = (code: string) => `teg.session.${code}`;
const ADMIN_KEY = 'teg.adminToken';
const canUseSessionStorage = () => typeof sessionStorage !== 'undefined';

export const useSessionStore = create<SessionState>((set) => ({
  session: null,
  adminToken: canUseSessionStorage() ? sessionStorage.getItem(ADMIN_KEY) : null,

  setSession: (session) => {
    if (canUseSessionStorage()) sessionStorage.setItem(keyFor(session.code), JSON.stringify(session));
    set({ session });
  },

  setAdminToken: (token) => {
    if (canUseSessionStorage()) sessionStorage.setItem(ADMIN_KEY, token);
    set({ adminToken: token });
  },

  restore: (code) => {
    try {
      if (!canUseSessionStorage()) return false;
      const raw = sessionStorage.getItem(keyFor(code));
      if (!raw) return false;
      set({ session: JSON.parse(raw) as PlayerSession });
      return true;
    } catch {
      return false;
    }
  },

  clear: () => set({ session: null }),
}));
