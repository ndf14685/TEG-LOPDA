import { z } from 'zod';

export const AICommentType = z.enum(['roast', 'praise', 'narration', 'drama', 'stats']);
export type AICommentType = z.infer<typeof AICommentType>;

export const AIComment = z.object({
  id: z.string(),
  type: AICommentType,
  text: z.string().max(500),
  targetPlayerId: z.string().nullable(),
  expression: z.enum(['neutral', 'smug', 'shocked', 'laughing', 'evil']).default('neutral'),
  audioAssetId: z.string().nullable().default(null),
  ts: z.number(),
});
export type AIComment = z.infer<typeof AIComment>;
