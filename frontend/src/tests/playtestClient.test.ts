import { describe, expect, it } from 'vitest';
import { redactForPlaytest } from '../services/playtest/playtestClient';

describe('playtestClient', () => {
  it('redacta tokens, secretos y objetivos', () => {
    const clean = redactForPlaytest({
      url: '/join/abcd/token-super-secreto?x=1',
      ws: '/ws/abcd?token=otro-secreto',
      adminToken: 'test-admin',
      your_objective: { target: 'secreto' },
    }) as Record<string, unknown>;
    const raw = JSON.stringify(clean);
    expect(raw).not.toContain('token-super-secreto');
    expect(raw).not.toContain('otro-secreto');
    expect(raw).not.toContain('test-admin');
    expect(raw).not.toContain('secreto');
  });
});
