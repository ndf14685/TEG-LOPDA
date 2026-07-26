import { describe, expect, it } from 'vitest';
import { AssetRegistry } from '../services/assets/AssetRegistry';
import { FALLBACK_SOUNDBOARD } from '../config/soundboard.config';

const ART_MANIFEST = {
  schema_version: '1.0',
  maps: {
    classic_50: { id: 'map.tactical.50', path: 'maps/base/map-world-canonical-50-003.svg' },
  },
  ui: { btn_attack: 'ui/buttons/button-action-attack-001.svg' },
};

const AUDIO_MANIFEST = {
  schema_version: '1.0',
  gameplay: { dice_roll: { path: 'audio/dice/sound-dice-roll-001.ogg', type: 'audio/ogg' } },
};

const TAUNTS_MANIFEST = {
  schema_version: '1.0',
  base_stamp_path: 'taunts/stamps/overlay-stamp-classified-001.webp',
  definitions: [
    { id: 'bardo_traicion', text: '¡TRAIDOR!', sound: 'audio/alerts/sound-alert-traitor-001.ogg' },
    { id: 'bardo_llora', text: 'LLORÁ EN DISCORD', sound: null },
  ],
};

function makeRegistry() {
  const r = new AssetRegistry();
  r.loadArtManifest(ART_MANIFEST);
  r.loadAudioManifest(AUDIO_MANIFEST);
  r.loadTauntsManifest(TAUNTS_MANIFEST);
  return r;
}

describe('AssetRegistry (manifiestos de Dirección de Arte)', () => {
  it('resuelve mapas por modo de juego y por id', () => {
    const r = makeRegistry();
    expect(r.mapUrl('classic_50')).toBe('/assets/maps/base/map-world-canonical-50-003.svg');
    expect(r.get('map.tactical.50')?.url).toBe('/assets/maps/base/map-world-canonical-50-003.svg');
    expect(r.mapUrl('mega_world_100')).toBeNull(); // no publicado aún
  });

  it('resuelve UI y audio con IDs dot-notation', () => {
    const r = makeRegistry();
    expect(r.get('ui.btn_attack')?.url).toContain('button-action-attack-001.svg');
    expect(r.get('audio.gameplay.dice_roll')?.kind).toBe('audio');
  });

  it('registra los faltantes sin romper', () => {
    const r = makeRegistry();
    expect(r.get('video.intro.001')).toBeNull();
    expect(r.getMissing()).toContain('video.intro.001');
  });

  it('el soundboard sale del taunts-manifest, con fallback local', () => {
    const r = makeRegistry();
    const buttons = r.soundboardButtons(FALLBACK_SOUNDBOARD);
    expect(buttons).toHaveLength(2);
    expect(buttons[0]).toEqual({ id: 'bardo_traicion', label: '¡TRAIDOR!', soundPath: 'audio/alerts/sound-alert-traitor-001.ogg' });

    const empty = new AssetRegistry();
    expect(empty.soundboardButtons(FALLBACK_SOUNDBOARD)).toBe(FALLBACK_SOUNDBOARD);
  });

  it('urlForPath normaliza los audio_asset_id del backend', () => {
    const r = makeRegistry();
    expect(r.urlForPath('audio/taunts/x.ogg')).toBe('/assets/audio/taunts/x.ogg');
    expect(r.urlForPath('/audio/taunts/x.ogg')).toBe('/assets/audio/taunts/x.ogg');
  });

  it('carga la paleta de marca y la valida', () => {
    const r = makeRegistry();
    r.loadPalette({
      theme: 'retro-tactical-dark',
      global: { bg: '#0D1117' },
      players: [{ id: 'p01', name: 'Rojo Alerta', hex: '#E63946' }],
    });
    expect(r.palette?.players[0].hex).toBe('#E63946');
    r.loadPalette({ nope: true });
    expect(r.palette?.theme).toBe('retro-tactical-dark'); // inválida no pisa la buena
  });

  it('manifiestos inválidos no rompen el registro', () => {
    const r = new AssetRegistry();
    r.loadArtManifest({ garbage: true });
    expect(r.mapUrl('classic_50')).toBeNull();
  });
});
