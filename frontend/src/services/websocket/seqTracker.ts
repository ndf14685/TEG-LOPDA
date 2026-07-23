/**
 * Trackea sequence_number de eventos PERSISTIDOS (monotónico ≥1 por partida).
 * Los efímeros (snapshot, presence.changed, error) llegan con 0 y no se trackean.
 * Un hueco => eventos perdidos => resincronizar (reconectar: el server manda
 * snapshot fresco en cada conexión).
 */
export class SeqTracker {
  private lastSeq: number | null = null;

  accept(seq: number): 'ok' | 'gap' | 'stale' {
    if (seq <= 0) return 'ok'; // efímero: no participa del stream ordenado
    if (this.lastSeq === null) {
      this.lastSeq = seq;
      return 'ok';
    }
    if (seq <= this.lastSeq) return 'stale';
    if (seq === this.lastSeq + 1) {
      this.lastSeq = seq;
      return 'ok';
    }
    return 'gap';
  }

  /** El snapshot trae recent_events; el último seq visto ancla el stream. */
  reset(seq: number | null): void {
    this.lastSeq = seq;
  }

  get current(): number | null {
    return this.lastSeq;
  }
}
