import { z } from 'zod';

/** Códigos del backend real: shared/contracts/api/error-codes.json */
export const ErrorCode = z.enum([
  'AUTH_FAILED',
  'FORBIDDEN',
  'NOT_FOUND',
  'INVALID_ACTION',
  'GAME_STATE_CONFLICT',
  'NOT_YOUR_TURN',
  'GAME_NOT_RUNNING',
  'INVALID_PAYLOAD',
  'MESSAGE_TOO_LARGE',
  'RATE_LIMITED',
]);
export type ErrorCode = z.infer<typeof ErrorCode>;

/** Todo error REST llega como {"detail": {"code", "message"}}. */
export const ApiErrorDetail = z.object({
  code: z.string(),
  message: z.string(),
});
export const ApiErrorResponse = z.object({ detail: ApiErrorDetail });
export type ApiErrorDetail = z.infer<typeof ApiErrorDetail>;
