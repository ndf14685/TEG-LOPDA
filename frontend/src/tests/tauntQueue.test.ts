import { describe, expect, it } from 'vitest';
import { TauntQueue, Cooldown } from '../services/audio/TauntQueue';

const tick = () => new Promise((r) => setTimeout(r, 0));

describe('TauntQueue', () => {
  it('reproduce en orden, nunca en paralelo', async () => {
    const q = new TauntQueue();
    const order: string[] = [];
    let concurrent = 0;
    let maxConcurrent = 0;

    const make = (id: string) => ({
      id,
      play: async () => {
        concurrent += 1;
        maxConcurrent = Math.max(maxConcurrent, concurrent);
        order.push(id);
        await tick();
        concurrent -= 1;
      },
    });

    q.enqueue(make('a'));
    q.enqueue(make('b'));
    q.enqueue(make('c'));
    await tick(); await tick(); await tick(); await tick();

    expect(order).toEqual(['a', 'b', 'c']);
    expect(maxConcurrent).toBe(1);
  });

  it('descarta los más viejos si la cola desborda', async () => {
    let release: () => void = () => {};
    const blocker = new Promise<void>((r) => { release = r; });
    const q = new TauntQueue(2);
    const played: string[] = [];
    const make = (id: string, wait = false) => ({
      id,
      play: async () => {
        played.push(id);
        if (wait) await blocker;
      },
    });

    q.enqueue(make('first', true)); // se está reproduciendo
    q.enqueue(make('x'));
    q.enqueue(make('y'));
    q.enqueue(make('z')); // desborda: x se descarta
    release();
    await tick(); await tick(); await tick();

    expect(played).toEqual(['first', 'y', 'z']);
  });

  it('un audio roto no frena la cola', async () => {
    const q = new TauntQueue();
    const played: string[] = [];
    q.enqueue({ id: 'broken', play: async () => { throw new Error('boom'); } });
    q.enqueue({ id: 'ok', play: async () => { played.push('ok'); } });
    await tick(); await tick();
    expect(played).toEqual(['ok']);
  });
});

describe('Cooldown', () => {
  it('bloquea reusos dentro de la ventana', () => {
    let now = 1000;
    const c = new Cooldown(5000, () => now);
    expect(c.tryUse()).toBe(true);
    now += 3000;
    expect(c.tryUse()).toBe(false);
    expect(c.remainingMs()).toBe(2000);
    now += 2001;
    expect(c.tryUse()).toBe(true);
  });
});
