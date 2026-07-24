import { describe, expect, it } from 'vitest';
import { useGameStore } from '../state/gameStore';

describe('estado canónico', () => {
  it('maneja stage y colocación', () => {
    const s = useGameStore.getState();
    s.setStage('placement_1');
    s.setPlacement(5, { t1: 2 });
    s.setPlacementDone(['p2']);
    const after = useGameStore.getState();
    expect(after.stage).toBe('placement_1');
    expect(after.placementRemaining).toBe(5);
    expect(after.placementPending).toEqual({ t1: 2 });
    expect(after.placementDone).toEqual(['p2']);
  });

  it('guarda acciones legales y objetivo del ganador', () => {
    const s = useGameStore.getState();
    s.setLegalActions([{ action: 'attack', params: {} }]);
    s.setFinishedObjective({ id: 'o', title: 'T', description: 'D' });
    const after = useGameStore.getState();
    expect(after.legalActions[0].action).toBe('attack');
    expect(after.finishedObjective?.title).toBe('T');
  });
});
