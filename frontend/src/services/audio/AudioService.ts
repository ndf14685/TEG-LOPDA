import { TauntQueue } from './TauntQueue';
import { assetRegistry } from '../assets/AssetRegistry';

export type AudioChannel = 'master' | 'music' | 'sfx' | 'taunts' | 'ai';

/**
 * Audio con desbloqueo por gesto de usuario (autoplay policy).
 * Archivos reales vía <audio> (rutas del AssetRegistry); tonos sintéticos
 * como fallback cuando el asset todavía no existe.
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

  playTestFanfare(): void {
    void this.playTonesAsync([440, 554, 659, 880], 0.12, 'sfx');
  }

  playDiceSound(): void {
    const asset = assetRegistry.get('audio.gameplay.dice_roll');
    if (asset) void this.playFile(asset.url, 'sfx').catch(() => this.playTonesAsync([196, 220], 0.06, 'sfx'));
    else void this.playTonesAsync([196, 220], 0.06, 'sfx');
  }

  /** Taunt del backend (audio_asset_id relativo a /assets). Encolado: nunca dos a la vez. */
  playTauntAsset(audioAssetId: string): void {
    const url = assetRegistry.urlForPath(audioAssetId);
    this.tauntQueue.enqueue({
      id: audioAssetId,
      play: () => this.playFile(url, 'taunts').catch(() => this.playTonesAsync([330, 392, 494], 0.1, 'taunts')),
    });
  }

  /** Sonido de botón del soundboard (path del taunts-manifest), si existe. */
  playSoundboardSound(soundPath: string | null): void {
    if (!soundPath) return;
    this.tauntQueue.enqueue({
      id: soundPath,
      play: () => this.playFile(assetRegistry.urlForPath(soundPath), 'taunts').catch(() => Promise.resolve()),
    });
  }

  private playFile(url: string, channel: AudioChannel): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.unlocked) return resolve();
      const gain = this.gainFor(channel);
      if (gain === 0) return resolve();
      const el = new Audio(url);
      el.volume = gain;
      el.onended = () => resolve();
      el.onerror = () => reject(new Error(`audio no disponible: ${url}`));
      el.play().catch(reject);
    });
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
