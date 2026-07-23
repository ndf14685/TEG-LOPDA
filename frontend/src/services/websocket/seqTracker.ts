/**
 * Trackea el sequence_number del stream de eventos por partida.
 * Un hueco => hay eventos perdidos => hay que pedir snapshot.
 */
export class SeqTracker {
  private lastSeq: number | null = null;

  /** Devuelve 'ok' | 'gap' | 'stale'. Los snapshots resetean con reset(). */
  accept(seq: number): 'ok' | 'gap' | 'stale' {
    if (this.lastSeq === null) {
      this.lastSeq = seq;
      return 'ok';
    }
    if (seq <= this.lastSeq) return 'stale';
    if (seq === this.lastSeq + 1) {
      this.lastSeq = seq;
      return 'ok';
    }
    // hueco: no avanzamos hasta resincronizar
    return 'gap';
  }

  reset(seq: number): void {
    this.lastSeq = seq;
  }

  get current(): number | null {
    return this.lastSeq;
  }
}
