import { describe, expect, it } from 'vitest';
import { AssetRegistry } from '../services/assets/AssetRegistry';

const MANIFEST = {
  version: '0.1.0',
  assets: [
    { id: 'avatar.general.001', kind: 'emoji' as const, src: '🪖', preload: false, fallbackId: null },
    { id: 'avatar.zorro.001', kind: 'emoji' as const, src: '🦊', preload: false, fallbackId: 'avatar.general.001' },
    { id: 'background.lobby.war-room.001', kind: 'image' as const, src: 'images/background-lobby-war-room-001.webp', preload: true, fallbackId: null },
  ],
};

function makeRegistry() {
  const registry = new AssetRegistry();
  registry.loadManifest(MANIFEST);
  return registry;
}

describe('AssetRegistry', () => {
  it('resuelve assets por ID dot-notation', () => {
    const r = makeRegistry();
    expect(r.get('avatar.zorro.001')?.src).toBe('🦊');
    expect(r.resolveSrc('background.lobby.war-room.001')).toBe('/assets/images/background-lobby-war-room-001.webp');
  });

  it('devuelve null y registra los faltantes', () => {
    const r = makeRegistry();
    expect(r.get('video.intro.001')).toBeNull();
    expect(r.getMissing()).toContain('video.intro.001');
  });

  it('sigue la cadena de fallback', () => {
    const r = makeRegistry();
    expect(r.fallbackFor('avatar.zorro.001')?.id).toBe('avatar.general.001');
    expect(r.fallbackFor('avatar.general.001')).toBeNull();
  });

  it('emoji() nunca rompe la UI', () => {
    const r = makeRegistry();
    expect(r.emoji('avatar.zorro.001')).toBe('🦊');
    expect(r.emoji('avatar.inexistente.001')).toBe('❔');
  });
});
