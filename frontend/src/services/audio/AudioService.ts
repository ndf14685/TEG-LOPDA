import { TauntQueue } from './TauntQueue';

export type AudioChannel = 'master' | 'music' | 'sfx' | 'taunts' | 'ai';

/**
 * Web Audio con desbloqueo por gesto de usuario (autoplay policy).
 * Hasta que unlock() corra tras una interacción, nada suena.
 */
class AudioService {
  private ctx: AudioContext | null = null;
  private unlocked = false;
  readonly tauntQueue = new TauntQueue();
  private volumes: Record<AudioChannel, number> = { master: 0.8, music: 0.6, sfx: 0.8, taunts: 0.9, ai: 0.8 };
  private muted: Record<AudioChannel, boolean> = { master: false, music: false, sfx: false, taunts: false, ai: false };

  /** Llamar desde un handler de click/keydown. Idempotente. */
  unlock(): void {
    if (this.unlocked) return;
    try {
      this.ctx = new AudioContext();
      void this.ctx.resume();
      this.unlocked = true;
    } catch {
      // sin audio; la app sigue
    }
  }

  get isUnlocked(): boolean {
    return this.unlocked;
  }

  setVolume(channel: AudioChannel, value: number): void {
    this.volumes[channel] = Math.min(1, Math.max(0, value));
  }

  setMuted(channel: AudioChannel, muted: boolean): void {
    this.muted[channel] = muted;
  }

  isMuted(channel: AudioChannel): boolean {
    return this.muted.master || this.muted[channel];
  }

  private gainFor(channel: AudioChannel): number {
    if (this.isMuted(channel)) return 0;
    return this.volumes.master * this.volumes[channel];
  }

  /** Fanfarria simple por osciladores: sirve para "probar audio" sin assets binarios. */
  playTestFanfare(): void {
    this.playTones([440, 554, 659, 880], 0.12, 'sfx');
  }

  playTauntBeep(): void {
    this.tauntQueue.enqueue({
      id: `beep-${Math.random().toString(36).slice(2)}`,
      play: () => this.playTonesAsync([330, 392, 494], 0.1, 'taunts'),
    });
  }

  private playTones(freqs: number[], noteSeconds: number, channel: AudioChannel): void {
    void this.playTonesAsync(freqs, noteSeconds, channel);
  }

  private playTonesAsync(freqs: number[], noteSeconds: number, channel: AudioChannel): Promise<void> {
    return new Promise((resolve) => {
      if (!this.ctx || !this.unlocked) return resolve();
      const gainValue = this.gainFor(channel);
      if (gainValue === 0) return resolve();
      const gain = this.ctx.createGain();
      gain.gain.value = gainValue * 0.2;
      gain.connect(this.ctx.destination);
      const start = this.ctx.currentTime;
      freqs.forEach((freq, i) => {
        const osc = this.ctx!.createOscillator();
        osc.type = 'triangle';
        osc.frequency.value = freq;
        osc.connect(gain);
        osc.start(start + i * noteSeconds);
        osc.stop(start + (i + 1) * noteSeconds);
      });
      setTimeout(resolve, freqs.length * noteSeconds * 1000 + 50);
    });
  }
}

export const audioService = new AudioService();
