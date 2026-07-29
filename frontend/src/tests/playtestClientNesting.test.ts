import { describe, expect, it, vi, beforeEach } from 'vitest';

// El bug: cada incidente guardaba una copia profunda del payload completo
// (que ya contenia recent_errors) dentro de recent_errors. Medido en
// data/playtest.db: de 6.965 B a 882.851 B duplicandose cada 20 s.

describe('playtestClient: recent_errors no crece de forma exponencial', () => {
  const posts: any[] = [];
  beforeEach(async () => {
    posts.length = 0;
    // playtestClient es singleton: limpiar estado acumulado entre tests.
    const { playtestClient } = await import('../services/playtest/playtestClient');
    (playtestClient as any).errors = [];
    (playtestClient as any).trail = [];
    vi.stubGlobal('fetch', vi.fn(async (_u: string, init: any) => {
      posts.push(JSON.parse(init.body));
      return { ok: true, status: 200, json: async () => ({}) };
    }));
    // entorno de test corre en 'node' (vitest.config.ts): sin jsdom hay que
    // stubear a mano lo que usa playtestClient.context() para armar el payload.
    const store = new Map<string, string>();
    vi.stubGlobal('sessionStorage', {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => void store.set(k, v),
      removeItem: (k: string) => void store.delete(k),
    });
    vi.stubGlobal('location', { href: 'http://localhost/test' });
    vi.stubGlobal('navigator', { userAgent: 'vitest' });
    vi.stubGlobal('innerWidth', 1024);
    vi.stubGlobal('innerHeight', 768);
    vi.stubGlobal('devicePixelRatio', 1);
  });

  it('el payload no crece mas que linealmente tras 10 incidentes', async () => {
    const { playtestClient } = await import('../services/playtest/playtestClient');
    (playtestClient as any).status = {
      active: true, mode: true, until: '', build: 'test',
      env: 'test', retention_days: 14, server_time_utc: '',
    };

    for (let i = 0; i < 10; i++) {
      playtestClient.reportTechnical({
        category: 'other', title: `err ${i}`,
        error_type: 'test', component: 'x',
      });
    }
    await vi.waitFor(() => expect(posts.length).toBe(10));

    const primero = JSON.stringify(posts[0]).length;
    const ultimo = JSON.stringify(posts[9]).length;
    // con el anidamiento esto daba mas de 100x
    expect(ultimo).toBeLessThan(primero * 4);
  });

  it('recent_errors solo guarda resumenes planos', async () => {
    const { playtestClient } = await import('../services/playtest/playtestClient');
    (playtestClient as any).status = {
      active: true, mode: true, until: '', build: 'test',
      env: 'test', retention_days: 14, server_time_utc: '',
    };

    playtestClient.reportTechnical({ category: 'other', title: 'a', error_type: 't', component: 'x' });
    playtestClient.reportTechnical({ category: 'other', title: 'b', error_type: 't', component: 'x' });
    await vi.waitFor(() => expect(posts.length).toBe(2));

    for (const err of posts[1].recent_errors ?? []) {
      expect(err).not.toHaveProperty('recent_errors');
      expect(err).not.toHaveProperty('action_trail');
    }
  });
});
