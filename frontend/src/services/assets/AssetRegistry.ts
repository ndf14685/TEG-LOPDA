import { ArtAssetsManifest, AudioManifest, TauntsManifest, BrandPalette, type GameMode, type SoundboardButton } from '@teg/contracts';
import { playtestClient } from '../playtest/playtestClient';

const ASSETS_BASE = '/assets/';
const MANIFESTS = {
  art: '/assets/manifest/assets-manifest.json',
  audio: '/assets/manifest/audio-manifest.json',
  taunts: '/assets/manifest/taunts-manifest.json',
  palette: '/assets/brand/palette/palette.json',
} as const;

export interface ResolvedAsset {
  id: string;
  kind: 'image' | 'audio' | 'svg';
  url: string;
}

/**
 * Registro central de assets. Fuente: los manifiestos de Dirección de Arte en
 * assets/manifest/ (ver assets/README-INTEGRATION.md). Los componentes piden
 * IDs dot-notation; acá se resuelven rutas, faltantes y fallbacks.
 */
export class AssetRegistry {
  private entries = new Map<string, ResolvedAsset>();
  private taunts: TauntsManifest | null = null;
  palette: BrandPalette | null = null;
  private missing = new Set<string>();
  loaded = false;

  async load(fetchFn: typeof fetch = fetch): Promise<void> {
    const [art, audio, taunts, palette] = await Promise.all([
      this.fetchJson(fetchFn, MANIFESTS.art),
      this.fetchJson(fetchFn, MANIFESTS.audio),
      this.fetchJson(fetchFn, MANIFESTS.taunts),
      this.fetchJson(fetchFn, MANIFESTS.palette),
    ]);
    if (art) this.loadArtManifest(art);
    if (audio) this.loadAudioManifest(audio);
    if (taunts) this.loadTauntsManifest(taunts);
    if (palette) this.loadPalette(palette);
    this.loaded = true;
  }

  loadPalette(raw: unknown): void {
    const parsed = BrandPalette.safeParse(raw);
    if (!parsed.success) return this.reportInvalid(MANIFESTS.palette);
    this.palette = parsed.data;
  }

  private async fetchJson(fetchFn: typeof fetch, path: string): Promise<unknown | null> {
    try {
      const res = await fetchFn(path);
      if (!res.ok) {
        playtestClient.reportTechnical({
          category: 'visual-problem',
          title: `Asset HTTP ${res.status}`,
          message: path,
          error_type: 'asset-http-error',
          component: 'AssetRegistry',
          endpoint: path,
          code: String(res.status),
        });
        throw new Error(`HTTP ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      if (typeof import.meta !== 'undefined' && import.meta.env?.DEV) {
        console.warn(`[assets] no se pudo cargar ${path}`, err);
      }
      return null;
    }
  }

  loadArtManifest(raw: unknown): void {
    const parsed = ArtAssetsManifest.safeParse(raw);
    if (!parsed.success) return this.reportInvalid(MANIFESTS.art);
    for (const [mode, map] of Object.entries(parsed.data.maps)) {
      this.entries.set(map.id, { id: map.id, kind: 'svg', url: ASSETS_BASE + map.path });
      this.entries.set(`map.mode.${mode}`, { id: `map.mode.${mode}`, kind: 'svg', url: ASSETS_BASE + map.path });
    }
    for (const [key, path] of Object.entries(parsed.data.ui)) {
      this.entries.set(`ui.${key}`, { id: `ui.${key}`, kind: 'image', url: ASSETS_BASE + path });
    }
  }

  loadAudioManifest(raw: unknown): void {
    const parsed = AudioManifest.safeParse(raw);
    if (!parsed.success) return this.reportInvalid(MANIFESTS.audio);
    const { schema_version: _v, ...categories } = parsed.data;
    for (const [category, sounds] of Object.entries(categories)) {
      for (const [name, def] of Object.entries(sounds)) {
        const id = `audio.${category}.${name}`;
        this.entries.set(id, { id, kind: 'audio', url: ASSETS_BASE + def.path });
      }
    }
  }

  loadTauntsManifest(raw: unknown): void {
    const parsed = TauntsManifest.safeParse(raw);
    if (!parsed.success) return this.reportInvalid(MANIFESTS.taunts);
    this.taunts = parsed.data;
  }

  get(id: string): ResolvedAsset | null {
    const entry = this.entries.get(id);
    if (entry) return entry;
    this.reportMissing(id);
    return null;
  }

  /** URL de un asset referenciado por path relativo del backend (ej: audio_asset_id de taunt.triggered). */
  urlForPath(relativePath: string): string {
    return ASSETS_BASE + relativePath.replace(/^\/+/, '');
  }

  /** Botones del soundboard desde taunts-manifest.json; fallback si Arte aún no lo publicó. */
  soundboardButtons(fallback: SoundboardButton[]): SoundboardButton[] {
    if (!this.taunts || this.taunts.definitions.length === 0) return fallback;
    return this.taunts.definitions.map((d) => ({ id: d.id, label: d.text, soundPath: d.sound }));
  }

  tauntStampUrl(): string | null {
    return this.taunts ? ASSETS_BASE + this.taunts.base_stamp_path : null;
  }

  mapUrl(mode: GameMode): string | null {
    return this.get(`map.mode.${mode}`)?.url ?? null;
  }

  getMissing(): string[] {
    return [...this.missing];
  }

  private reportMissing(id: string): void {
    if (this.missing.has(id)) return;
    this.missing.add(id);
    if (typeof import.meta !== 'undefined' && import.meta.env?.DEV) {
      console.warn(`[assets] asset faltante: ${id}`);
    }
    playtestClient.reportTechnical({
      category: 'visual-problem',
      title: `Asset faltante: ${id}`,
      message: id,
      error_type: 'asset-missing',
      component: 'AssetRegistry',
    });
  }

  private reportInvalid(path: string): void {
    if (typeof import.meta !== 'undefined' && import.meta.env?.DEV) {
      console.error(`[assets] manifest inválido: ${path}`);
    }
    playtestClient.reportTechnical({
      category: 'visual-problem',
      title: `Manifest inválido: ${path}`,
      message: path,
      error_type: 'asset-manifest-invalid',
      component: 'AssetRegistry',
      endpoint: path,
    });
  }
}

export const assetRegistry = new AssetRegistry();
