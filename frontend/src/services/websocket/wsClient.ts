import { ServerEnvelope, SERVER_EVENT_SCHEMAS, type ServerEventType, type ClientMessage } from '@teg/contracts';
import { SeqTracker } from './seqTracker';

type Handler = (payload: unknown, envelope: ServerEnvelope) => void;
type StatusListener = (status: WsStatus) => void;
export type WsStatus = 'idle' | 'connecting' | 'open' | 'reconnecting' | 'closed';

const BASE_DELAY_MS = 500;
const MAX_DELAY_MS = 10_000;

/**
 * Cliente WebSocket singleton: valida eventos con zod, trackea seq,
 * pide snapshot ante huecos y reconecta con backoff exponencial + jitter.
 */
class WsClient {
  private ws: WebSocket | null = null;
  private sessionId: string | null = null;
  private handlers = new Map<string, Set<Handler>>();
  private statusListeners = new Set<StatusListener>();
  private seq = new SeqTracker();
  private retries = 0;
  private intentionalClose = false;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  status: WsStatus = 'idle';

  connect(sessionId: string): void {
    if (this.ws && this.sessionId === sessionId && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) return;
    this.sessionId = sessionId;
    this.intentionalClose = false;
    this.open();
  }

  private open(): void {
    if (!this.sessionId) return;
    this.setStatus(this.retries > 0 ? 'reconnecting' : 'connecting');
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${proto}://${location.host}/ws?session=${encodeURIComponent(this.sessionId)}`);
    this.ws = ws;

    ws.onopen = () => {
      this.retries = 0;
      this.setStatus('open');
      // Al reconectar el stream de seq del server siguió sin nosotros: pedir snapshot siempre.
      this.send({ type: 'sync.request' });
    };

    ws.onmessage = (event) => this.handleMessage(String(event.data));

    ws.onclose = () => {
      if (this.intentionalClose) {
        this.setStatus('closed');
        return;
      }
      const delay = Math.min(BASE_DELAY_MS * 2 ** this.retries, MAX_DELAY_MS) * (0.7 + Math.random() * 0.6);
      this.retries += 1;
      this.setStatus('reconnecting');
      this.reconnectTimer = setTimeout(() => this.open(), delay);
    };
  }

  private handleMessage(raw: string): void {
    let envelope: ServerEnvelope;
    try {
      envelope = ServerEnvelope.parse(JSON.parse(raw));
    } catch {
      if (import.meta.env.DEV) console.warn('[ws] evento con sobre inválido descartado');
      return;
    }

    const schema = SERVER_EVENT_SCHEMAS[envelope.type as ServerEventType];
    if (!schema) {
      if (import.meta.env.DEV) console.warn(`[ws] tipo de evento desconocido: ${envelope.type}`);
      return;
    }
    const payload = schema.safeParse(envelope.payload);
    if (!payload.success) {
      if (import.meta.env.DEV) console.warn(`[ws] payload inválido para ${envelope.type}`, payload.error);
      return;
    }

    if (envelope.type === 'game.snapshot' || envelope.type === 'game.started') {
      this.seq.reset(envelope.seq);
    } else {
      const verdict = this.seq.accept(envelope.seq);
      if (verdict === 'stale') return;
      if (verdict === 'gap') {
        this.emit('sync.lost', null, envelope);
        this.send({ type: 'sync.request' });
        return;
      }
    }

    this.emit(envelope.type, payload.data, envelope);
  }

  private emit(type: string, payload: unknown, envelope: ServerEnvelope): void {
    for (const handler of this.handlers.get(type) ?? []) handler(payload, envelope);
    for (const handler of this.handlers.get('*') ?? []) handler(payload, envelope);
  }

  send(msg: ClientMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(JSON.stringify(msg));
  }

  on(type: ServerEventType | 'sync.lost' | '*', handler: Handler): () => void {
    if (!this.handlers.has(type)) this.handlers.set(type, new Set());
    this.handlers.get(type)!.add(handler);
    return () => this.handlers.get(type)?.delete(handler);
  }

  onStatus(listener: StatusListener): () => void {
    this.statusListeners.add(listener);
    listener(this.status);
    return () => this.statusListeners.delete(listener);
  }

  private setStatus(status: WsStatus): void {
    this.status = status;
    for (const l of this.statusListeners) l(status);
  }

  disconnect(): void {
    this.intentionalClose = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
    this.sessionId = null;
  }
}

export const wsClient = new WsClient();
