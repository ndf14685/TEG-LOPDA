import { GameEventEnvelope, EVENT_PAYLOAD_SCHEMAS, type KnownEventType, type ClientMessage } from '@teg/contracts';
import { SeqTracker } from './seqTracker';
import { playtestClient } from '../playtest/playtestClient';

type Handler = (payload: unknown, envelope: GameEventEnvelope) => void;
type StatusListener = (status: WsStatus) => void;
export type WsStatus = 'idle' | 'connecting' | 'open' | 'reconnecting' | 'closed' | 'revoked';

const BASE_DELAY_MS = 500;
const MAX_DELAY_MS = 10_000;
const PING_INTERVAL_MS = 20_000;
/** Close codes del backend que NO deben reintentar: auth/kick. */
const FATAL_CLOSE_CODES = new Set([4401, 4403, 4001]);

/**
 * Cliente del WS real: /ws/{code}?token=...
 * - El server manda game.snapshot al conectar: reconectar ES resincronizar.
 * - Valida sobres y payloads con zod; eventos desconocidos pasan con payload opaco.
 * - Hueco de sequence_number => fuerza reconexión (no hay sync.request).
 */
class WsClient {
  private ws: WebSocket | null = null;
  private code: string | null = null;
  private token: string | null = null;
  private handlers = new Map<string, Set<Handler>>();
  private statusListeners = new Set<StatusListener>();
  private seq = new SeqTracker();
  private retries = 0;
  private intentionalClose = false;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private pendingTimers = new Set<ReturnType<typeof setTimeout>>();
  status: WsStatus = 'idle';

  connect(code: string, token: string): void {
    if (
      this.ws && this.code === code && this.token === token &&
      (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)
    ) return;
    this.disconnect();
    this.code = code;
    this.token = token;
    this.intentionalClose = false;
    this.retries = 0;
    this.open();
  }

  private open(): void {
    if (!this.code || !this.token) return;
    this.setStatus(this.retries > 0 ? 'reconnecting' : 'connecting');
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${proto}://${location.host}/ws/${this.code}?token=${encodeURIComponent(this.token)}`);
    this.ws = ws;

    ws.onopen = () => {
      this.retries = 0;
      this.seq.reset(null); // el snapshot entrante re-ancla el stream
      this.setStatus('open');
      playtestClient.track(this.retries > 0 ? 'websocket.reconnected' : 'websocket.connected', { code: this.code });
      this.startPing();
    };

    ws.onmessage = (event) => this.handleMessage(String(event.data));

    ws.onclose = (event) => {
      this.stopPing();
      if (this.intentionalClose) {
        this.setStatus('closed');
        return;
      }
      playtestClient.reportTechnical({
        category: 'connection-problem',
        title: `WebSocket cerrado ${event.code || ''}`,
        message: event.reason || `close:${event.code}`,
        error_type: 'websocket.close',
        component: 'wsClient',
        code: String(event.code),
      });
      if (FATAL_CLOSE_CODES.has(event.code)) {
        this.setStatus('revoked');
        return;
      }
      const delay = Math.min(BASE_DELAY_MS * 2 ** this.retries, MAX_DELAY_MS) * (0.7 + Math.random() * 0.6);
      this.retries += 1;
      this.setStatus('reconnecting');
      this.reconnectTimer = setTimeout(() => this.open(), delay);
    };
  }

  /** Reconexión dura: el server responde con snapshot fresco. */
  resync(): void {
    if (this.intentionalClose) return;
    this.ws?.close();
  }

  private handleMessage(raw: string): void {
    // cualquier byte que llegue del server prueba que la conexión está viva:
    // eso es exactamente lo que el temporizador de acción pendiente quiere
    // detectar, así que se cancela acá antes de intentar parsear nada. Si
    // esto corriera después de un `return` temprano (JSON inválido, envelope
    // inválido), un mensaje real pero descartado dejaría vivo el timer y
    // dispararía el mismo incidente falso pending-action-timeout que esta
    // tarea vino a eliminar.
    this.clearPendingTimers();

    let data: unknown;
    try {
      data = JSON.parse(raw);
    } catch {
      playtestClient.reportTechnical({
        category: 'other',
        title: 'WebSocket JSON inválido',
        message: 'No se pudo parsear mensaje WebSocket',
        error_type: 'websocket-json-parse',
        component: 'wsClient',
      });
      return;
    }
    // único mensaje no-envelope del server
    if (typeof data === 'object' && data !== null && (data as { type?: string }).type === 'pong') return;

    const parsed = GameEventEnvelope.safeParse(data);
    if (!parsed.success) {
      playtestClient.reportTechnical({
        category: 'other',
        title: 'Envelope WebSocket inválido',
        message: parsed.error.issues[0]?.message ?? 'envelope inválido',
        error_type: 'contract-parse-error',
        component: 'wsClient',
      });
      if (import.meta.env.DEV) console.warn('[ws] sobre inválido descartado', parsed.error.issues[0]);
      return;
    }
    const envelope = parsed.data;

    const verdict = this.seq.accept(envelope.sequence_number);
    if (verdict === 'stale') return;
    if (verdict === 'gap') {
      playtestClient.reportTechnical({
        category: 'desynchronization',
        title: 'Salto de sequence_number',
        message: `sequence gap at ${envelope.sequence_number}`,
        error_type: 'sequence-gap',
        component: 'wsClient',
        event_id: envelope.event_id,
        sequence_number: envelope.sequence_number,
      });
      this.emit('sync.lost', null, envelope);
      this.resync();
      return;
    }

    const schema = EVENT_PAYLOAD_SCHEMAS[envelope.event_type as KnownEventType];
    let payload: unknown = envelope.payload;
    if (schema) {
      const result = schema.safeParse(envelope.payload);
      if (!result.success) {
        playtestClient.reportTechnical({
          category: 'other',
          title: `Payload inválido: ${envelope.event_type}`,
          message: result.error.issues[0]?.message ?? 'payload inválido',
          error_type: 'contract-parse-error',
          component: 'wsClient',
          event_id: envelope.event_id,
          sequence_number: envelope.sequence_number,
        });
        if (import.meta.env.DEV) console.warn(`[ws] payload inválido para ${envelope.event_type}`, result.error.issues[0]);
        return;
      }
      payload = result.data;
    }

    this.emit(envelope.event_type, payload, envelope);
  }

  private clearPendingTimers(): void {
    for (const timer of this.pendingTimers) clearTimeout(timer);
    this.pendingTimers.clear();
  }

  private emit(type: string, payload: unknown, envelope: GameEventEnvelope): void {
    for (const handler of this.handlers.get(type) ?? []) handler(payload, envelope);
    for (const handler of this.handlers.get('*') ?? []) handler(payload, envelope);
  }

  send(msg: ClientMessage): void {
    playtestClient.track(`${msg.type}.requested`, { payload: (msg as any).payload ?? {} });
    // si el socket no está abierto el mensaje se descarta: no tiene sentido
    // esperar una resolución que nunca pedimos
    if (this.ws?.readyState !== WebSocket.OPEN) return;
    const pending = setTimeout(() => {
      this.pendingTimers.delete(pending);
      playtestClient.reportTechnical({
        category: 'action-did-not-work',
        title: `Acción pendiente sin resolución: ${msg.type}`,
        message: `Sin evento de resolución luego de 8s`,
        error_type: 'pending-action-timeout',
        component: 'wsClient',
        action: msg.type,
      });
    }, 8000);
    this.pendingTimers.add(pending);
    this.ws.send(JSON.stringify(msg));
  }

  on(type: KnownEventType | 'sync.lost' | '*' | (string & {}), handler: Handler): () => void {
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

  private startPing(): void {
    this.stopPing();
    this.pingTimer = setInterval(() => this.send({ type: 'ping' }), PING_INTERVAL_MS);
  }

  private stopPing(): void {
    if (this.pingTimer) clearInterval(this.pingTimer);
    this.pingTimer = null;
  }

  disconnect(): void {
    this.intentionalClose = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.stopPing();
    this.ws?.close();
    this.ws = null;
    this.code = null;
    this.token = null;
  }
}

export const wsClient = new WsClient();
