import { AssetManifest, type AssetEntry } from '@teg/contracts';

const ASSETS_BASE = '/assets/';
const MANIFEST_PATH = '/assets/manifests/assets-manifest.json';

/**
 * Registro central de assets. Único punto de resolución de rutas:
 * los componentes piden IDs dot-notation, nunca rutas.
 */
export class AssetRegistry {
  private entries = new Map<string, AssetEntry>();
  private loaded = false;
  private missing = new Set<string>();

  async load(fetchFn: typeof fetch = fetch): Promise<void> {
    try {
      const res = await fetchFn(MANIFEST_PATH);
      const manifest = AssetManifest.parse(await res.json());
      this.loadManifest(manifest);
    } catch (err) {
      // Un manifest roto no debe tirar la app: seguimos con registro vacío + fallbacks.
      if (typeof import.meta !== 'undefined' && import.meta.env?.DEV) {
        console.error('[assets] no se pudo cargar el manifest', err);
      }
      this.loaded = true;
    }
  }

  loadManifest(manifest: AssetManifest): void {
    for (const entry of manifest.assets) this.entries.set(entry.id, entry);
    this.loaded = true;
  }

  /** Resuelve un asset por ID. Devuelve null (y lo registra como faltante) si no existe. */
  get(id: string): AssetEntry | null {
    const entry = this.entries.get(id);
    if (entry) return entry;
    this.reportMissing(id);
    return null;
  }

  /**
   * Fallback para cuando un asset existe en el manifest pero falla al cargar
   * (archivo ausente, error de red). Sigue la cadena fallbackId con protección de ciclos.
   */
  fallbackFor(id: string): AssetEntry | null {
    const seen = new Set<string>([id]);
    let current = this.entries.get(id);
    while (current?.fallbackId && !seen.has(current.fallbackId)) {
      seen.add(current.fallbackId);
      const next = this.entries.get(current.fallbackId);
      if (next) return next;
      current = undefined;
    }
    return null;
  }

  /** URL final para assets de archivo; para emoji devuelve el glifo. */
  resolveSrc(id: string): string | null {
    const entry = this.get(id);
    if (!entry) return null;
    return entry.kind === 'emoji' ? entry.src : ASSETS_BASE + entry.src;
  }

  /** Emoji directo con fallback visible para no romper UI. */
  emoji(id: string, fallbackGlyph = '❔'): string {
    const entry = this.get(id);
    return entry?.kind === 'emoji' ? entry.src : fallbackGlyph;
  }

  getMissing(): string[] {
    return [...this.missing];
  }

  preloadCritical(): void {
    for (const entry of this.entries.values()) {
      if (!entry.preload || entry.kind === 'emoji') continue;
      if (entry.kind === 'image') {
        const img = new Image();
        img.src = ASSETS_BASE + entry.src;
      }
      // audio/video pesados se cargan diferido, a demanda
    }
  }

  private reportMissing(id: string): void {
    if (this.missing.has(id)) return;
    this.missing.add(id);
    if (typeof import.meta !== 'undefined' && import.meta.env?.DEV) {
      console.warn(`[assets] asset faltante: ${id}`);
    }
  }
}

export const assetRegistry = new AssetRegistry();
