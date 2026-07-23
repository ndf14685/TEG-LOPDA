import { z } from 'zod';

export const ErrorCode = z.enum([
  'TOKEN_INVALID',
  'TOKEN_REVOKED',
  'TOKEN_EXPIRED',
  'GAME_NOT_FOUND',
  'GAME_ALREADY_STARTED',
  'PLAYER_NOT_FOUND',
  'NOT_ADMIN',
  'VERSION_MISMATCH',
  'RATE_LIMITED',
  'VALIDATION_ERROR',
  'INTERNAL_ERROR',
]);
export type ErrorCode = z.infer<typeof ErrorCode>;

export const ApiError = z.object({
  code: ErrorCode,
  message: z.string(),
});
export type ApiError = z.infer<typeof ApiError>;
