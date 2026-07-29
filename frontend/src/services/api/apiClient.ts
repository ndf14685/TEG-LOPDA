import type { z } from 'zod';
import {
  HealthResponse,
  CreateGameResponse,
  AdminGameDetailResponse,
  InvitePlayerResponse,
  RegenerateTokenResponse,
  StartGameResponse,
  OkResponse,
  JoinPreviewResponse,
  JoinConfirmResponse,
  ApiErrorResponse,
  CreateProfileResponse,
  ProfileListResponse,
  ProfileTokenResponse,
  ResolveProfileResponse,
  type CreateGameRequest,
  type InvitePlayerRequest,
  type CommentatorConfigRequest,
} from '@teg/contracts';
import { playtestClient } from '../playtest/playtestClient';

export class ApiRequestError extends Error {
  constructor(public readonly code: string, message: string, public readonly status: number) {
    super(message);
  }
}

async function request<S extends z.ZodTypeAny>(schema: S, path: string, init?: RequestInit): Promise<z.output<S>> {
  const requestId = crypto.randomUUID();
  const res = await fetch(path, {
    ...init,
    headers: { 'content-type': 'application/json', 'x-request-id': requestId, ...(init?.headers ?? {}) },
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const parsed = ApiErrorResponse.safeParse(body);
    const code = parsed.success ? parsed.data.detail.code : 'INTERNAL_ERROR';
    const message = parsed.success ? parsed.data.detail.message : `Error HTTP ${res.status}`;
    playtestClient.reportTechnical({
      category: res.status >= 500 ? 'other' : 'action-did-not-work',
      title: `HTTP ${res.status}: ${path}`,
      message,
      error_type: 'http-error',
      component: 'apiClient',
      endpoint: path,
      code,
      request_id: requestId,
    });
    if (parsed.success) throw new ApiRequestError(code, message, res.status);
    throw new ApiRequestError('INTERNAL_ERROR', `Error HTTP ${res.status}`, res.status);
  }
  const parsedBody = schema.safeParse(body);
  if (!parsedBody.success) {
    playtestClient.reportTechnical({
      category: 'other',
      title: `Contrato REST inválido: ${path}`,
      message: parsedBody.error.issues[0]?.message ?? 'parse error',
      error_type: 'contract-parse-error',
      component: 'apiClient',
      endpoint: path,
      request_id: requestId,
    });
    throw parsedBody.error;
  }
  return parsedBody.data;
}

const adminHeaders = (adminToken: string) => ({ 'x-admin-token': adminToken });

export const api = {
  health: () => request(HealthResponse, '/health'),

  // ---- join (público, token en URL) ----
  joinPreview: (code: string, token: string) =>
    request(JoinPreviewResponse, `/api/join/${code}/${encodeURIComponent(token)}`),

  joinConfirm: (code: string, token: string, nickname?: string | null) =>
    request(JoinConfirmResponse, `/api/join/${code}/${encodeURIComponent(token)}`, {
      method: 'POST',
      body: JSON.stringify({ nickname: nickname ?? null }),
    }),

  // ---- admin (X-Admin-Token global del servidor) ----
  createGame: (adminToken: string, body: CreateGameRequest) =>
    request(CreateGameResponse, '/api/admin/games', {
      method: 'POST',
      headers: adminHeaders(adminToken),
      body: JSON.stringify(body),
    }),

  gameDetail: (adminToken: string, gameId: string) =>
    request(AdminGameDetailResponse, `/api/admin/games/${gameId}`, { headers: adminHeaders(adminToken) }),

  invitePlayer: (adminToken: string, gameId: string, body: InvitePlayerRequest) =>
    request(InvitePlayerResponse, `/api/admin/games/${gameId}/players`, {
      method: 'POST',
      headers: adminHeaders(adminToken),
      body: JSON.stringify(body),
    }),

  regenerateToken: (adminToken: string, gameId: string, playerId: string) =>
    request(RegenerateTokenResponse, `/api/admin/games/${gameId}/players/${playerId}/regenerate-token`, {
      method: 'POST',
      headers: adminHeaders(adminToken),
    }),

  convertToAi: (adminToken: string, gameId: string, playerId: string) =>
    request(OkResponse, `/api/admin/games/${gameId}/players/${playerId}/convert-to-ai`, {
      method: 'POST',
      headers: adminHeaders(adminToken),
    }),

  kickPlayer: (adminToken: string, gameId: string, playerId: string) =>
    request(OkResponse, `/api/admin/games/${gameId}/players/${playerId}/kick`, {
      method: 'POST',
      headers: adminHeaders(adminToken),
    }),

  startGame: (adminToken: string, gameId: string) =>
    request(StartGameResponse, `/api/admin/games/${gameId}/start`, {
      method: 'POST',
      headers: adminHeaders(adminToken),
    }),

  pauseGame: (adminToken: string, gameId: string) =>
    request(OkResponse, `/api/admin/games/${gameId}/pause`, { method: 'POST', headers: adminHeaders(adminToken) }),

  // ---- perfiles persistentes del grupo ----
  createProfile: (adminToken: string, body: { nickname: string; color?: string | null }) =>
    request(CreateProfileResponse, '/api/admin/profiles', {
      method: 'POST',
      headers: adminHeaders(adminToken),
      body: JSON.stringify(body),
    }),

  listProfiles: (adminToken: string) =>
    request(ProfileListResponse, '/api/admin/profiles', { headers: adminHeaders(adminToken) }),

  regenerateProfileToken: (adminToken: string, profileId: string) =>
    request(ProfileTokenResponse, `/api/admin/profiles/${profileId}/regenerate-token`, {
      method: 'POST',
      headers: adminHeaders(adminToken),
    }),

  resolveProfile: (token: string) =>
    request(ResolveProfileResponse, `/api/profile/${encodeURIComponent(token)}`),

  configureCommentator: (adminToken: string, gameId: string, body: CommentatorConfigRequest) =>
    fetch(`/api/admin/games/${gameId}/commentator`, {
      method: 'POST',
      headers: { 'content-type': 'application/json', ...adminHeaders(adminToken) },
      body: JSON.stringify(body),
    }),
};

/**
 * Los join_url del backend usan su public_base_url (ej: http://localhost:8123).
 * Para compartir/navegar usamos siempre el origin del frontend, mismo path.
 */
export function toFrontendUrl(backendUrl: string): string {
  try {
    const url = new URL(backendUrl);
    return location.origin + url.pathname;
  } catch {
    return backendUrl;
  }
}
