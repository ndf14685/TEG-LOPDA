import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { wsClient } from '../services/websocket/wsClient';
import { bindWsToStores } from '../services/websocket/bindStores';
import { useSessionStore } from '../state/sessionStore';
import { useGameStore } from '../state/gameStore';
import { useConnectionStore } from '../state/connectionStore';
import { MapPanel } from '../components/map/MapPanel';
import { TurnPhaseBar } from '../components/game/TurnPhaseBar';
import { AICommentatorPanel } from '../components/ai-commentator/AICommentatorPanel';
import { ChatPanel } from '../components/chat/ChatPanel';
import { SoundboardBar } from '../components/audio/SoundboardBar';
import { ConnectionBanner } from '../components/ConnectionBanner';
import { PlayerAvatar } from '../components/players/PlayerAvatar';
import { colorValue } from '../utils/playerColors';
import { audioService } from '../services/audio/AudioService';
import { CombatOverlay } from '../components/dice/CombatOverlay';
import { Dice3D } from '../components/dice/Dice3D';
import { PostGameModal } from '../components/game/PostGameModal';

export function GamePage() {
  const { code = '' } = useParams();
  const navigate = useNavigate();
  const session = useSessionStore((s) => s.session);
  const restore = useSessionStore((s) => s.restore);
  const game = useGameStore((s) => s.game);
  const players = useGameStore((s) => s.players);
  const turn = useGameStore((s) => s.turn);
  const stage = useGameStore((s) => s.stage);
  const placementRemaining = useGameStore((s) => s.placementRemaining);
  const placementDone = useGameStore((s) => s.placementDone);
  const lastDice = useGameStore((s) => s.lastDice);
  const lastAttack = useGameStore((s) => s.lastAttack);
  const finished = useGameStore((s) => s.finished);
  const lastError = useGameStore((s) => s.lastError);
  const playerById = useGameStore((s) => s.playerById);
  const currentPlayerId = useGameStore((s) => s.currentPlayerId);
  const syncState = useConnectionStore((s) => s.syncState);
  const selectedSource = useGameStore((s) => s.selectedSourceTerritory);
  const selectedTarget = useGameStore((s) => s.selectedTargetTerritory);
  const territories = useGameStore((s) => s.territories);
  const [attackTarget, setAttackTarget] = useState('');
  const [fortifyCount, setFortifyCount] = useState(1);
  const setSelectedSource = useGameStore((s) => s.setSelectedSourceTerritory);
  const setSelectedTarget = useGameStore((s) => s.setSelectedTargetTerritory);

  useEffect(() => {
    if (selectedTarget && territories[selectedTarget]?.owner_player_id) {
      setAttackTarget(territories[selectedTarget].owner_player_id!);
    }
  }, [selectedTarget, territories]);

  useEffect(() => {
    if ((!session || session.code !== code) && !restore(code)) navigate('/');
  }, [session, code, restore, navigate]);

  useEffect(() => {
    if (!session || session.code !== code) return;
    bindWsToStores();
    wsClient.connect(code, session.token);
  }, [session, code]);

  if (!session) return null;

  const currentId = currentPlayerId();
  const current = playerById(currentId);
  const myTurn = currentId === session.playerId;
  const actionsBlocked = syncState !== 'synced' || game?.status !== 'running';
  const combatants = players.filter((p) => (p.role === 'player' || p.role === 'admin' || p.role === 'ai_player') && !p.eliminated);
  const targets = combatants.filter((p) => p.id !== session.playerId);
  const diceRoller = lastDice ? playerById(lastDice.playerId) : undefined;

  function send(action: () => void) {
    audioService.unlock();
    action();
  }

  return (
    <main className="flex h-screen flex-col" data-testid="game-board">
      <ConnectionBanner />

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-3 p-3 lg:grid-cols-[230px_1fr_300px]">
        {/* izquierda: ejércitos */}
        <aside className="hidden min-h-0 flex-col gap-2 overflow-y-auto lg:flex">
          <h2 className="text-xs font-semibold tracking-wider text-stone-400">EJÉRCITOS</h2>
          {combatants.map((p) => (
            <div key={p.id} className={`rounded-lg border bg-war-900 px-3 py-2 ${currentId === p.id ? 'border-gold-500' : 'border-war-700'}`}>
              <div className="flex items-center gap-2">
                <PlayerAvatar avatarAssetId={p.avatar_asset_id} role={p.role} color={p.color} size="sm" />
                <span className="truncate text-sm font-semibold" style={{ color: colorValue(p.color) }}>{p.nickname}</span>
                {p.role === 'ai_player' && <span className="rounded bg-war-700 px-1 text-[10px]">🤖 IA</span>}
              </div>
              <p className="mt-1 text-xs text-stone-400">
                {p.presence === 'online' ? '🟢' : p.presence === 'reconnecting' ? '🟡' : '⚫'} {p.presence ?? '—'}
              </p>
            </div>
          ))}
        </aside>

        {/* centro: mapa y barra de fases */}
        <section className="relative flex min-h-0 flex-col gap-2">
          {stage === 'placement_1' || stage === 'placement_2' ? (
            <div className="rounded-lg border border-amber-700 bg-amber-950/60 px-4 py-2 text-center" data-testid="placement-banner">
              <p className="font-bold text-amber-300">
                {stage === 'placement_1' ? 'Colocación inicial: 5 ejércitos' : 'Segunda ronda: 3 ejércitos'}
              </p>
              <p className="text-sm text-stone-300">
                {placementRemaining > 0
                  ? `Te quedan ${placementRemaining} por colocar — tocá tus países`
                  : 'Listo. Esperando al resto…'}
              </p>
              <p className="text-xs text-stone-400">
                {placementDone.length}/{combatants.length} jugadores terminaron
              </p>
            </div>
          ) : (
            <TurnPhaseBar />
          )}
          <div className="relative min-h-0 flex-1 rounded-xl border border-war-700 bg-war-900 overflow-hidden">
            <MapPanel />
            {actionsBlocked && game?.status === 'paused' && (
              <div className="absolute inset-0 z-10 flex items-center justify-center rounded-xl bg-war-950/70">
                <p className="rounded-lg bg-war-800 px-4 py-2 text-sm">⏸️ Partida pausada por el admin</p>
              </div>
            )}
            {syncState !== 'synced' && (
              <div className="absolute inset-0 z-10 flex items-center justify-center rounded-xl bg-war-950/70">
                <p className="rounded-lg bg-war-800 px-4 py-2 text-sm">⏳ Sincronizando — acciones bloqueadas</p>
              </div>
            )}
          </div>
        </section>

        {/* derecha: turno, acciones, resultados, IA */}
        <aside className="flex min-h-0 flex-col gap-3 overflow-y-auto">
          <div className="rounded-lg border border-war-700 bg-war-900 p-3" data-testid="turn-panel">
            <h2 className="mb-1 text-xs font-semibold tracking-wider text-stone-400">TURNO {turn?.turn_number ?? '—'}</h2>
            {current ? (
              <p className="text-sm">
                Juega <strong style={{ color: colorValue(current.color) }}>{current.nickname}</strong>
                {myTurn && <span className="text-gold-400"> — ¡sos vos!</span>}
              </p>
            ) : (
              <p className="text-sm text-stone-500">…</p>
            )}
          </div>

          {session.role !== 'spectator' && stage !== 'placement_1' && stage !== 'placement_2' && (
            <div className="rounded-lg border border-war-700 bg-war-900 p-3" data-testid="actions-panel">
              <h2 className="mb-2 text-xs font-semibold tracking-wider text-stone-400">ACCIONES</h2>
              <div className="flex flex-col gap-2">
                <button
                  disabled={actionsBlocked || !myTurn}
                  onClick={() => send(() => wsClient.send({ type: 'dice.roll', payload: { count: 3 } }))}
                  data-testid="roll-dice"
                  className="rounded-lg bg-gold-500 px-3 py-2 text-sm font-bold text-war-950 hover:bg-gold-400 disabled:opacity-30"
                >
                  🎲 Dados de práctica (sin efecto)
                </button>

                {/* Acción táctica sobre la selección del mapa */}
                {selectedSource && selectedTarget && (() => {
                  const targetIsMine = territories[selectedTarget]?.owner_player_id === session.playerId;
                  const maxMove = Math.max(1, (territories[selectedSource]?.armies ?? 1) - 1);
                  const clearSelection = () => { setSelectedSource(null); setSelectedTarget(null); };
                  return (
                    <div className="rounded-md border border-red-900/50 bg-red-950/40 p-2 text-xs">
                      <p className="font-semibold text-red-300">
                        {targetIsMine ? '🛡️ Reagrupar:' : '⚔️ Ataque táctico:'}
                      </p>
                      <p className="text-stone-300 truncate">
                        {selectedSource.replace('territory-', '').replaceAll('-', ' ')} →{' '}
                        <span className="font-bold text-gold-400">{selectedTarget.replace('territory-', '').replaceAll('-', ' ')}</span>
                      </p>
                      {!targetIsMine ? (
                        <button
                          disabled={actionsBlocked || !myTurn || turn?.phase !== 'attack'}
                          onClick={() => send(() => wsClient.send({
                            type: 'attack',
                            payload: {
                              source_territory_id: selectedSource,
                              target_territory_id: selectedTarget,
                              attacker_dice: 3,
                            },
                          }))}
                          data-testid="attack-territory"
                          className="mt-2 w-full rounded-lg bg-red-700 px-3 py-1.5 text-sm font-bold text-red-50 hover:bg-red-600 disabled:opacity-30"
                        >
                          ⚔️ Atacar{turn?.phase !== 'attack' ? ' (pasá a fase de ataque)' : ''}
                        </button>
                      ) : (
                        <div className="mt-2 flex items-center gap-2">
                          <input
                            type="number"
                            min={1}
                            max={maxMove}
                            value={Math.min(fortifyCount, maxMove)}
                            onChange={(e) => setFortifyCount(Math.max(1, Number(e.target.value) || 1))}
                            aria-label="Ejércitos a mover"
                            className="w-16 rounded border border-war-700 bg-war-800 px-2 py-1 text-sm"
                          />
                          <button
                            disabled={actionsBlocked || !myTurn || turn?.phase !== 'fortify'}
                            onClick={() => send(() => {
                              wsClient.send({
                                type: 'turn.fortify',
                                payload: {
                                  source_territory_id: selectedSource,
                                  target_territory_id: selectedTarget,
                                  count: Math.min(fortifyCount, maxMove),
                                },
                              });
                              clearSelection();
                            })}
                            data-testid="fortify-button"
                            className="flex-1 rounded-lg bg-sky-700 px-3 py-1.5 text-sm font-bold text-sky-50 hover:bg-sky-600 disabled:opacity-30"
                          >
                            🛡️ Mover{turn?.phase !== 'fortify' ? ' (pasá a reagrupar)' : ''}
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })()}

                <div className="flex gap-2">
                  <select
                    value={attackTarget}
                    onChange={(e) => setAttackTarget(e.target.value)}
                    aria-label="Objetivo del ataque"
                    className="min-w-0 flex-1 rounded border border-war-700 bg-war-800 px-2 py-1.5 text-sm"
                  >
                    <option value="">Atacar a…</option>
                    {targets.map((p) => <option key={p.id} value={p.id}>{p.nickname}</option>)}
                  </select>
                  <button
                    disabled={actionsBlocked || !myTurn || !attackTarget}
                    onClick={() => send(() => wsClient.send({ type: 'attack', payload: { target_player_id: attackTarget, attacker_dice: 3 } }))}
                    data-testid="attack-button"
                    className="rounded-lg bg-red-700 px-3 py-1.5 text-sm font-bold text-red-50 hover:bg-red-600 disabled:opacity-30"
                  >
                    ⚔️
                  </button>
                </div>
                <button
                  disabled={actionsBlocked || !myTurn}
                  onClick={() => send(() => wsClient.send({ type: 'turn.end' }))}
                  data-testid="end-turn"
                  className="rounded-lg border border-war-700 bg-war-800 px-3 py-1.5 text-sm hover:border-gold-500 disabled:opacity-30"
                >
                  Terminar turno →
                </button>
              </div>
              {lastError && Date.now() - lastError.at < 6000 && (
                <p role="alert" className="mt-2 text-xs text-red-400">{lastError.message}</p>
              )}
            </div>
          )}

          {lastDice && (
            <div className="rounded-lg border border-war-700 bg-war-900 p-3" data-testid="dice-result">
              <h2 className="mb-2 text-xs font-semibold tracking-wider text-stone-400">DADOS DE TIRADA</h2>
              <p className="mb-2 text-xs">
                <span style={{ color: colorValue(diceRoller?.color) }}>{diceRoller?.nickname ?? '???'}</span> sacó:
              </p>
              <div className="flex gap-2 justify-center">
                {lastDice.dice.map((d, i) => (
                  <Dice3D key={i} value={d} variant="attacker" size="sm" />
                ))}
              </div>
            </div>
          )}

          {lastAttack && (
            <div className="rounded-lg border border-war-700 bg-war-900 p-3" data-testid="attack-result">
              <h2 className="mb-2 text-xs font-semibold tracking-wider text-stone-400">ÚLTIMA BATALLA</h2>
              <div className="flex items-center justify-between text-xs mb-2">
                <span style={{ color: colorValue(playerById(lastAttack.attackerId)?.color) }}>
                  {playerById(lastAttack.attackerId)?.nickname ?? '???'} (−{lastAttack.attackerLosses})
                </span>
                <span className="text-red-400 font-bold">VS</span>
                <span style={{ color: colorValue(playerById(lastAttack.defenderId)?.color) }}>
                  {playerById(lastAttack.defenderId)?.nickname ?? '???'} (−{lastAttack.defenderLosses})
                </span>
              </div>
              <div className="flex justify-around items-center pt-1">
                <div className="flex gap-1">
                  {lastAttack.attackerDice.map((d, i) => (
                    <Dice3D key={i} value={d} variant="attacker" size="sm" />
                  ))}
                </div>
                <span className="text-stone-500 font-bold">:</span>
                <div className="flex gap-1">
                  {lastAttack.defenderDice.map((d, i) => (
                    <Dice3D key={i} value={d} variant="defender" size="sm" />
                  ))}
                </div>
              </div>
            </div>
          )}

          <AICommentatorPanel />
        </aside>
      </div>

      {/* Overlay modal de batalla táctica 3D */}
      <CombatOverlay />

      {/* Modal Infografía de Trofeos Post-Partida */}
      <PostGameModal />

      <footer className="grid gap-3 border-t border-war-700 bg-war-900/60 p-3 lg:grid-cols-[1fr_380px]">
        <div>
          <h2 className="mb-1.5 text-xs font-semibold tracking-wider text-stone-400">BARDEO RÁPIDO</h2>
          <SoundboardBar />
        </div>
        <ChatPanel compact />
      </footer>
    </main>
  );
}
