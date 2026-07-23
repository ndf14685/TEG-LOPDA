import { z } from 'zod';

/** Emociones que emite el comentarista del backend (ai/commentator.py). */
export const CommentEmotion = z.enum(['neutral', 'mocking', 'excited', 'dramatic', 'deadpan']).catch('neutral');
export type CommentEmotion = z.infer<typeof CommentEmotion>;

/** Comentario ya normalizado para la UI (payload de ai.comment.generated + metadata del sobre). */
export interface AICommentView {
  id: string; // event_id
  text: string;
  emotion: string;
  audioAsset: string | null;
  targetPlayerId: string | null;
  ts: string;
}
