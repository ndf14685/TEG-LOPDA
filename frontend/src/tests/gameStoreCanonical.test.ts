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

  it('eco optimista de colocación: baja el pool y sube el pendiente del país', () => {
    const s = useGameStore.getState();
    s.setPlacement(3, {});
    s.optimisticPlace('t1');
    let after = useGameStore.getState();
    expect(after.placementRemaining).toBe(2);
    expect(after.placementPending).toEqual({ t1: 1 });
    s.optimisticPlace('t1');
    after = useGameStore.getState();
    expect(after.placementRemaining).toBe(1);
    expect(after.placementPending).toEqual({ t1: 2 });
  });

  it('eco optimista no baja de cero cuando el pool está agotado', () => {
    const s = useGameStore.getState();
    s.setPlacement(0, { t1: 5 });
    s.optimisticPlace('t1');
    const after = useGameStore.getState();
    expect(after.placementRemaining).toBe(0);
    expect(after.placementPending).toEqual({ t1: 5 });
  });

  it('reinforceBatch por defecto 1 y actualizable', () => {
    expect(useGameStore.getState().reinforceBatch).toBe(1);
    useGameStore.getState().setReinforceBatch(5);
    expect(useGameStore.getState().reinforceBatch).toBe(5);
    useGameStore.getState().setReinforceBatch(1);
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
