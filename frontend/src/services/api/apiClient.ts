import type { z } from 'zod';
import {
  HealthResponse,
  CreateGameResponse,
  SessionResponse,
  AdminGameView,
  PlayerLink,
  type CreateGameRequest,
  type CreatePlayerRequest,
  ApiError,
} from '@teg/contracts';

export class ApiRequestError extends Error {
  constructor(public readonly code: string, message: string, public readonly status: number) {
    super(message);
  }
}

async function request<S extends z.ZodTypeAny>(schema: S, path: string, init?: RequestInit): Promise<z.output<S>> {
  const res = await fetch(path, {
    ...init,
    headers: { 'content-type': 'application/json', ...(init?.headers ?? {}) },
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const parsed = ApiError.safeParse(body);
    if (parsed.success) throw new ApiRequestError(parsed.data.code, parsed.data.message, res.status);
    throw new ApiRequestError('INTERNAL_ERROR', `Error HTTP ${res.status}`, res.status);
  }
  return schema.parse(body);
}

export const api = {
  health: () => request(HealthResponse, '/api/health'),

  createGame: (body: CreateGameRequest) =>
    request(CreateGameResponse, '/api/games', { method: 'POST', body: JSON.stringify(body) }),

  adminView: (gameId: string, adminToken: string) =>
    request(AdminGameView, `/api/games/${gameId}/admin`, { headers: { 'x-admin-token': adminToken } }),

  createPlayer: (gameId: string, adminToken: string, body: CreatePlayerRequest) =>
    request(PlayerLink, `/api/games/${gameId}/players`, {
      method: 'POST',
      headers: { 'x-admin-token': adminToken },
      body: JSON.stringify(body),
    }),

  revokeLink: (gameId: string, adminToken: string, playerId: string) =>
    request(PlayerLink, `/api/games/${gameId}/players/${playerId}/revoke`, {
      method: 'POST',
      headers: { 'x-admin-token': adminToken },
    }),

  regenerateLink: (gameId: string, adminToken: string, playerId: string) =>
    request(PlayerLink, `/api/games/${gameId}/players/${playerId}/regenerate`, {
      method: 'POST',
      headers: { 'x-admin-token': adminToken },
    }),

  createSession: (token: string) =>
    request(SessionResponse, '/api/session', { method: 'POST', body: JSON.stringify({ token }) }),

  confirmNickname: (sessionId: string, nickname: string) =>
    fetch(`/api/session/${sessionId}/nickname`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ nickname }),
    }),
};
