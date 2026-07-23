import express from 'express';
import { createServer } from 'node:http';
import { WebSocketServer, WebSocket } from 'ws';
import { nanoid } from 'nanoid';
import {
  PROTOCOL_VERSION,
  CreateGameRequest,
  CreatePlayerRequest,
  SessionRequest,
  ConfirmNicknameRequest,
  ClientMessage,
  GameSettings,
} from '@teg/contracts';
import type { AIComment, ServerEnvelope } from '@teg/contracts';
import { games, sessions, createGame, createPlayer, findByToken, publicPlayer, dealTerritories, snapshot, type GameRecord, type PlayerRecord } from './store.js';

const PORT = Number(process.env.PORT ?? 8790);
const COUNTDOWN_MS = 2400;
const TAUNT_COOLDOWN_MS = 5000;
const startedAt = Date.now();

const app = express();
app.use(express.json({ limit: '64kb' }));

const sockets = new Map<string, Set<WebSocket>>(); // gameId -> sockets

function fail(res: express.Response, status: number, code: string, message: string) {
  res.status(status).json({ code, message });
}

function adminFrom(req: express.Request): { game: GameRecord; player: PlayerRecord } | null {
  const token = req.header('x-admin-token');
  if (!token) return null;
  const found = findByToken(token);
  if (!found || found.player.role !== 'admin' || found.player.revoked) return null;
  return found;
}

function broadcast(game: GameRecord, type: string, payload: unknown) {
  game.seq += 1;
  const envelope: ServerEnvelope = { v: PROTOCOL_VERSION, seq: game.seq, type, ts: Date.now(), payload };
  const msg = JSON.stringify(envelope);
  for (const ws of sockets.get(game.id) ?? []) {
    if (ws.readyState === WebSocket.OPEN) ws.send(msg);
  }
}

function sendTo(ws: WebSocket, game: GameRecord, type: string, payload: unknown) {
  // Mensajes dirigidos reutilizan el seq actual sin incrementarlo: no son parte del stream ordenado.
  const envelope: ServerEnvelope = { v: PROTOCOL_VERSION, seq: game.seq, type, ts: Date.now(), payload };
  if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(envelope));
}

function lobbyPayload(game: GameRecord) {
  return {
    gameId: game.id,
    gameName: game.name,
    status: game.status,
    players: [...game.players.values()].map(publicPlayer),
  };
}

// ---------- API ----------

app.get('/api/health', (_req, res) => {
  res.json({ ok: true, protocolVersion: PROTOCOL_VERSION, uptimeSeconds: (Date.now() - startedAt) / 1000 });
});

app.post('/api/games', (req, res) => {
  const parsed = CreateGameRequest.safeParse(req.body);
  if (!parsed.success) return fail(res, 400, 'VALIDATION_ERROR', parsed.error.message);
  const { gameName, admin, settings } = parsed.data;
  const game = createGame(gameName, GameSettings.parse(settings ?? {}));
  const adminPlayer = createPlayer(
    game,
    { name: admin.name, nickname: admin.nickname, color: admin.color, avatarId: admin.avatarId, tauntAudioIds: [], trustLevel: 10, titles: ['Fundador'], relationships: {} },
    'admin',
  );
  res.json({ gameId: game.id, adminToken: adminPlayer.token, adminPlayerId: adminPlayer.id });
});

app.get('/api/games/:gameId/admin', (req, res) => {
  const auth = adminFrom(req);
  if (!auth || auth.game.id !== req.params.gameId) return fail(res, 403, 'NOT_ADMIN', 'Token de admin inválido');
  const game = auth.game;
  res.json({
    gameId: game.id,
    gameName: game.name,
    links: [...game.players.values()].map((p) => ({
      playerId: p.id,
      token: p.token,
      joinPath: `/join/${game.id}/${p.token}`,
      revoked: p.revoked,
      profile: p.profile,
      role: p.role,
    })),
  });
});

app.post('/api/games/:gameId/players', (req, res) => {
  const auth = adminFrom(req);
  if (!auth || auth.game.id !== req.params.gameId) return fail(res, 403, 'NOT_ADMIN', 'Token de admin inválido');
  const parsed = CreatePlayerRequest.safeParse(req.body);
  if (!parsed.success) return fail(res, 400, 'VALIDATION_ERROR', parsed.error.message);
  const player = createPlayer(auth.game, parsed.data.profile, parsed.data.role);
  broadcast(auth.game, 'lobby.state', lobbyPayload(auth.game));
  res.json({ playerId: player.id, token: player.token, joinPath: `/join/${auth.game.id}/${player.token}`, revoked: false });
});

app.post('/api/games/:gameId/players/:playerId/revoke', (req, res) => {
  const auth = adminFrom(req);
  if (!auth || auth.game.id !== req.params.gameId) return fail(res, 403, 'NOT_ADMIN', 'Token de admin inválido');
  const player = auth.game.players.get(req.params.playerId);
  if (!player) return fail(res, 404, 'PLAYER_NOT_FOUND', 'Jugador inexistente');
  player.revoked = true;
  res.json({ playerId: player.id, token: player.token, joinPath: `/join/${auth.game.id}/${player.token}`, revoked: true });
});

app.post('/api/games/:gameId/players/:playerId/regenerate', (req, res) => {
  const auth = adminFrom(req);
  if (!auth || auth.game.id !== req.params.gameId) return fail(res, 403, 'NOT_ADMIN', 'Token de admin inválido');
  const player = auth.game.players.get(req.params.playerId);
  if (!player) return fail(res, 404, 'PLAYER_NOT_FOUND', 'Jugador inexistente');
  player.token = nanoid(24);
  player.revoked = false;
  res.json({ playerId: player.id, token: player.token, joinPath: `/join/${auth.game.id}/${player.token}`, revoked: false });
});

app.post('/api/session', (req, res) => {
  const parsed = SessionRequest.safeParse(req.body);
  if (!parsed.success) return fail(res, 400, 'VALIDATION_ERROR', parsed.error.message);
  const found = findByToken(parsed.data.token);
  if (!found) return fail(res, 404, 'TOKEN_INVALID', 'Ese link no corresponde a ninguna partida.');
  if (found.player.revoked) return fail(res, 403, 'TOKEN_REVOKED', 'El link fue revocado por el administrador.');
  const sessionId = `s-${nanoid(20)}`;
  sessions.set(sessionId, { gameId: found.game.id, playerId: found.player.id });
  res.json({
    sessionId,
    gameId: found.game.id,
    playerId: found.player.id,
    role: found.player.role,
    profile: found.player.profile,
    protocolVersion: PROTOCOL_VERSION,
  });
});

app.post('/api/session/:sessionId/nickname', (req, res) => {
  const session = sessions.get(req.params.sessionId);
  if (!session) return fail(res, 401, 'TOKEN_INVALID', 'Sesión inválida');
  const parsed = ConfirmNicknameRequest.safeParse(req.body);
  if (!parsed.success) return fail(res, 400, 'VALIDATION_ERROR', parsed.error.message);
  const game = games.get(session.gameId);
  const player = game?.players.get(session.playerId);
  if (!game || !player) return fail(res, 404, 'PLAYER_NOT_FOUND', 'Jugador inexistente');
  player.profile.nickname = parsed.data.nickname;
  broadcast(game, 'lobby.state', lobbyPayload(game));
  res.json({ ok: true });
});

// ---------- WebSocket ----------

const httpServer = createServer(app);
const wss = new WebSocketServer({ server: httpServer, path: '/ws' });

wss.on('connection', (ws, req) => {
  const url = new URL(req.url ?? '', 'http://localhost');
  const session = sessions.get(url.searchParams.get('session') ?? '');
  const game = session ? games.get(session.gameId) : undefined;
  const player = game?.players.get(session?.playerId ?? '');
  if (!session || !game || !player || player.revoked) {
    ws.send(JSON.stringify({ v: PROTOCOL_VERSION, seq: 0, type: 'error', ts: Date.now(), payload: { code: 'TOKEN_INVALID', message: 'Sesión inválida o revocada' } }));
    ws.close();
    return;
  }

  if (!sockets.has(game.id)) sockets.set(game.id, new Set());
  sockets.get(game.id)!.add(ws);
  player.connected = true;
  player.everJoined = true;

  broadcast(game, 'lobby.state', lobbyPayload(game));
  if (game.status === 'in-game') sendTo(ws, game, 'game.snapshot', { snapshot: snapshot(game) });

  ws.on('message', (raw) => {
    let msg: ClientMessage;
    try {
      msg = ClientMessage.parse(JSON.parse(String(raw)));
    } catch {
      sendTo(ws, game, 'error', { code: 'VALIDATION_ERROR', message: 'Mensaje inválido' });
      return;
    }

    switch (msg.type) {
      case 'player.ready':
        player.ready = msg.ready;
        broadcast(game, 'lobby.state', lobbyPayload(game));
        break;

      case 'chat.send':
        if (!player.muted) broadcast(game, 'chat.message', { playerId: player.id, text: msg.text.slice(0, 300), ts: Date.now() });
        break;

      case 'sync.request':
        sendTo(ws, game, 'game.snapshot', { snapshot: snapshot(game) });
        break;

      case 'taunt.trigger': {
        const now = Date.now();
        if (player.muted || now - player.lastTauntAt < TAUNT_COOLDOWN_MS) return;
        player.lastTauntAt = now;
        broadcast(game, 'taunt.triggered', { fromPlayerId: player.id, soundboardId: msg.soundboardId, text: msg.soundboardId, audioAssetId: null });
        break;
      }

      case 'game.start': {
        if (player.role !== 'admin' || game.status !== 'lobby') return;
        game.status = 'starting';
        broadcast(game, 'game.starting', { countdownMs: COUNTDOWN_MS });
        setTimeout(() => {
          game.status = 'in-game';
          dealTerritories(game);
          broadcast(game, 'game.started', { snapshot: snapshot(game) });
          scheduleMockAIComment(game);
        }, COUNTDOWN_MS);
        break;
      }
    }
  });

  ws.on('close', () => {
    sockets.get(game.id)?.delete(ws);
    player.connected = false;
    broadcast(game, 'lobby.state', lobbyPayload(game));
  });
});

function scheduleMockAIComment(game: GameRecord) {
  if (!game.settings.aiCommentatorEnabled) return;
  const commentId = `c-${nanoid(8)}`;
  setTimeout(() => broadcast(game, 'ai.comment.typing', { commentId }), 800);
  setTimeout(() => {
    const victims = [...game.players.values()].filter((p) => p.role === 'player');
    const victim = victims[0] ?? [...game.players.values()][0];
    const comment: AIComment = {
      id: commentId,
      type: 'roast',
      text: `Arranca la guerra y ${victim?.profile.nickname ?? 'alguien'} ya mira el mapa como si entendiera algo. Spoiler: no.`,
      targetPlayerId: victim?.id ?? null,
      expression: 'smug',
      audioAssetId: null,
      ts: Date.now(),
    };
    broadcast(game, 'ai.comment.generated', { comment });
  }, 2200);
}

httpServer.listen(PORT, () => {
  console.log(`[server-mock] escuchando en http://localhost:${PORT} (protocolo ${PROTOCOL_VERSION})`);
});
