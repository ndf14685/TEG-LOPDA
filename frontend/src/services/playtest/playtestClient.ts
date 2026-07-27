import { useConnectionStore } from '../../state/connectionStore';
import { useGameStore } from '../../state/gameStore';
import { useSessionStore } from '../../state/sessionStore';

type Severity = 'impide seguir' | 'dificulta jugar' | 'molesto' | 'detalle menor';

export interface PlaytestStatus {
  active: boolean;
  mode: boolean;
  until: string;
  build: string;
  env: string;
  retention_days: number;
  server_time_utc: string;
}

const SESSION_KEY = 'teg.playtest.sessionId';
const TRAIL_LIMIT = 50;
const ERROR_LIMIT = 20;
const MANUAL_WINDOW_MS = 60_000;
const MANUAL_LIMIT = 5;

function getSessionId(): string {
  let id = sessionStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    sessionStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

export function redactForPlaytest(value: unknown): unknown {
  if (typeof value === 'string') {
    return value
      .replace(/(\/join\/[^/]+\/)[^/?#\s]+/g, '$1***')
      .replace(/(\/ws\/[^?]+\?token=)[^&#\s]+/g, '$1***')
      .replace(/(token|secret|password|admin)=([^&\s]+)/gi, '$1=***');
  }
  if (Array.isArray(value)) return value.slice(0, 100).map(redactForPlaytest);
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      const lk = k.toLowerCase();
      if (lk.includes('token') || lk.includes('secret') || lk.includes('password')) out[k] = '***';
      else if (lk.includes('objective')) out[k] = '[redacted-secret-objective]';
      else out[k] = redactForPlaytest(v);
    }
    return out;
  }
  return value;
}

function context() {
  const session = useSessionStore.getState().session;
  const game = useGameStore.getState();
  const conn = useConnectionStore.getState();
  return {
    session_id: getSessionId(),
    game_id: session?.gameId ?? game.game?.id ?? null,
    player_id: session?.playerId ?? game.youId ?? null,
    player_alias: session?.nickname ?? game.playerById(game.youId)?.nickname ?? null,
    build_version: playtestClient.status?.build ?? 'unknown',
    timestamp_local: new Date().toString(),
      url: redactForPlaytest(location.href),
    viewport: { width: innerWidth, height: innerHeight, dpr: devicePixelRatio },
    browser: navigator.userAgent,
    context: {
      turn: game.turn,
      phase: game.turn?.phase ?? null,
      active_player_id: game.currentPlayerId(),
      selected_source: game.selectedSourceTerritory,
      selected_target: game.selectedTargetTerritory,
      connection: { ws: conn.wsStatus, sync: conn.syncState },
      last_combat: game.battle,
      last_error: game.lastError,
    },
  };
}

class PlaytestClient {
  status: PlaytestStatus | null = null;
  private trail: Record<string, unknown>[] = [];
  private errors: Record<string, unknown>[] = [];
  private manualTimes: number[] = [];

  async init(): Promise<void> {
    try {
      const res = await fetch('/api/playtest/status');
      this.status = await res.json();
    } catch {
      this.status = { active: false, mode: false, until: '', build: 'unknown', env: 'unknown', retention_days: 14, server_time_utc: '' };
    }
    if (!this.status?.active) return;
    await this.registerSession();
    this.installGlobalHandlers();
    this.track('playtest.started', { build: this.status.build });
  }

  get active(): boolean {
    return Boolean(this.status?.active);
  }

  async registerSession(): Promise<void> {
    if (!this.active) return;
    await this.post('/api/playtest/sessions', {
      ...context(),
      user_agent: navigator.userAgent,
    });
  }

  track(action_type: string, data: Record<string, unknown> = {}, event?: { event_id?: string; sequence_number?: number }): void {
    if (!this.active) return;
    const item = {
      action_type,
      timestamp_utc: new Date().toISOString(),
      event_id: event?.event_id,
      sequence_number: event?.sequence_number,
      data: redactForPlaytest(data),
    };
    this.trail.push(item);
    this.trail = this.trail.slice(-TRAIL_LIMIT);
  }

  reportTechnical(input: Record<string, unknown>): void {
    if (!this.active) return;
    const payload = {
      ...context(),
      ...input,
      action_trail: this.trail,
      recent_errors: this.errors,
    };
    this.errors.push(redactForPlaytest(payload) as Record<string, unknown>);
    this.errors = this.errors.slice(-ERROR_LIMIT);
    void this.post('/api/playtest/incidents', payload);
  }

  async reportManual(input: {
    category: string;
    description: string;
    expected?: string;
    perceivedSeverity: Severity;
    screenshotDataUrl?: string | null;
  }): Promise<string> {
    if (!this.active) throw new Error('Modo playtest inactivo');
    const now = Date.now();
    this.manualTimes = this.manualTimes.filter((t) => now - t < MANUAL_WINDOW_MS);
    if (this.manualTimes.length >= MANUAL_LIMIT) throw new Error('Demasiados reportes por minuto.');
    this.manualTimes.push(now);
    const res = await this.post('/api/playtest/incidents', {
      ...context(),
      category: input.category,
      title: input.description.slice(0, 140),
      message: input.description,
      severity: input.perceivedSeverity === 'impide seguir' ? 'BLOCKER' : input.perceivedSeverity === 'dificulta jugar' ? 'MAJOR' : 'MINOR',
      error_type: 'manual-report',
      component: 'frontend.manual-report',
      context: { ...context().context, expected: input.expected ?? '' },
      action_trail: this.trail,
      recent_errors: this.errors,
      screenshot_data_url: input.screenshotDataUrl ?? null,
    });
    this.track('manual_report.created', { incident_id: res.incident_id, category: input.category });
    return res.incident_id;
  }

  private installGlobalHandlers(): void {
    window.addEventListener('error', (event) => {
      this.reportTechnical({
        category: 'other',
        title: `Frontend error: ${event.message}`,
        message: event.message,
        error_type: 'window.onerror',
        component: String(event.filename || 'frontend'),
        context: { line: event.lineno, column: event.colno, stack: event.error?.stack },
      });
    });
    window.addEventListener('unhandledrejection', (event) => {
      this.reportTechnical({
        category: 'other',
        title: 'Unhandled promise rejection',
        message: event.reason?.message || String(event.reason),
        error_type: 'unhandledrejection',
        component: 'frontend.promise',
        context: { stack: event.reason?.stack },
      });
    });
    window.addEventListener('beforeunload', () => {
      const game = useGameStore.getState();
      if (game.targetingMode || game.battle?.open || game.radialMenu) {
        this.track('page.reload_during_active_action', { targetingMode: game.targetingMode, battleOpen: game.battle?.open });
      }
    });
  }

  private async post(path: string, body: Record<string, unknown>): Promise<any> {
    const res = await fetch(path, {
      method: 'POST',
      headers: { 'content-type': 'application/json', 'x-request-id': crypto.randomUUID() },
      body: JSON.stringify(redactForPlaytest(body)),
    });
    if (!res.ok) throw new Error(`PLAYTEST_HTTP_${res.status}`);
    return res.json();
  }
}

export const playtestClient = new PlaytestClient();
