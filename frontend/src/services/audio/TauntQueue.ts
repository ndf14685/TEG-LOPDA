export interface QueuedTaunt {
  id: string;
  play: () => Promise<void>;
}

/**
 * Cola secuencial: nunca suenan dos taunts a la vez.
 * Si la cola supera maxPending se descartan los más viejos (anti-caos).
 */
export class TauntQueue {
  private queue: QueuedTaunt[] = [];
  private playing = false;

  constructor(private readonly maxPending = 3) {}

  enqueue(taunt: QueuedTaunt): void {
    this.queue.push(taunt);
    while (this.queue.length > this.maxPending) this.queue.shift();
    void this.drain();
  }

  get pending(): number {
    return this.queue.length;
  }

  get isPlaying(): boolean {
    return this.playing;
  }

  private async drain(): Promise<void> {
    if (this.playing) return;
    this.playing = true;
    while (this.queue.length > 0) {
      const next = this.queue.shift()!;
      try {
        await next.play();
      } catch {
        // un audio roto no frena la cola
      }
    }
    this.playing = false;
  }
}

/** Cooldown por acción (soundboard anti-spam). */
export class Cooldown {
  private lastAt = Number.NEGATIVE_INFINITY;

  constructor(private readonly ms: number, private readonly now: () => number = Date.now) {}

  tryUse(): boolean {
    const t = this.now();
    if (t - this.lastAt < this.ms) return false;
    this.lastAt = t;
    return true;
  }

  remainingMs(): number {
    return Math.max(0, this.ms - (this.now() - this.lastAt));
  }
}
