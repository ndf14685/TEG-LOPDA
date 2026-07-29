import { afterEach, describe, expect, it, vi } from 'vitest';
import { playtestClient, redactForPlaytest } from '../services/playtest/playtestClient';

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  playtestClient.status = null;
});

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

  it('mantiene el trail local sin publicar una request por cada accion', () => {
    playtestClient.status = {
      active: true,
      mode: true,
      until: '2026-07-28T23:59:59-03:00',
      build: 'test-build',
      env: 'test',
      retention_days: 14,
      server_time_utc: new Date().toISOString(),
    };
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    playtestClient.track('turn.started', { token: 'secret' });

    expect(fetchMock).not.toHaveBeenCalled();
  });
});
