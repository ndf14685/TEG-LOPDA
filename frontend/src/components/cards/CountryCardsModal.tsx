import { useState } from 'react';
import { useGameStore } from '../../state/gameStore';
import { wsClient } from '../../services/websocket/wsClient';
import { audioService } from '../../services/audio/AudioService';

const SYMBOL_ICON: Record<string, string> = {
  ship: '🚢',
  cannon: '💣',
  balloon: '🎈',
  joker: '🃏',
};

const SYMBOL_NAME: Record<string, string> = {
  ship: 'Barco',
  cannon: 'Cañón',
  balloon: 'Globo',
  joker: 'Comodín',
};

export function CountryCardsModal() {
  const cards = useGameStore((s) => s.cards);
  const turn = useGameStore((s) => s.turn);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  function toggleCard(id: string) {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((item) => item !== id));
    } else if (selectedIds.length < 3) {
      setSelectedIds([...selectedIds, id]);
    }
  }

  function handleTrade() {
    if (selectedIds.length !== 3) return;
    audioService.unlock();
    wsClient.send({
      type: 'cards.trade',
      payload: { card_ids: selectedIds },
    });
    setSelectedIds([]);
    setIsOpen(false);
  }

  return (
    <>
      {/* Botón flotante para abrir Tarjetas */}
      <button
        onClick={() => setIsOpen(true)}
        className="relative flex items-center gap-1.5 rounded-lg border border-gold-500/40 bg-war-900 px-3 py-1.5 text-xs font-bold text-gold-400 hover:bg-war-800 shadow-md"
      >
        <span>🃏 Tarjetas</span>
        {cards.length > 0 && (
          <span className="flex h-4 w-4 items-center justify-center rounded-full bg-gold-500 text-[10px] text-war-950 font-black">
            {cards.length}
          </span>
        )}
      </button>

      {/* Modal de Tarjetas */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-war-950/80 p-4 backdrop-blur-md">
          <div className="w-full max-w-xl rounded-2xl border border-war-700 bg-war-900 p-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-war-700 pb-3">
              <div className="flex items-center gap-2">
                <span className="text-2xl">🃏</span>
                <div>
                  <h3 className="font-display text-lg font-bold text-gold-400">TARJETAS DE PAÍS</h3>
                  <p className="text-xs text-stone-400">Canjeá 3 tarjetas iguales o 3 distintas por tropas de refuerzo</p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="text-stone-400 hover:text-stone-100 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            {cards.length === 0 ? (
              <div className="my-8 text-center text-sm text-stone-500">
                <p className="text-4xl mb-2">📜</p>
                <p>Todavía no tenés tarjetas de país.</p>
                <p className="text-xs text-stone-600 mt-1">Conquistá al menos 1 territorio en tu turno para obtener una tarjeta.</p>
              </div>
            ) : (
              <div className="my-4 grid grid-cols-2 sm:grid-cols-3 gap-3">
                {cards.map((card) => {
                  const isSelected = selectedIds.includes(card.id);
                  const territoryName = card.territory_id.replace('territory-', '').replaceAll('-', ' ');

                  return (
                    <div
                      key={card.id}
                      onClick={() => toggleCard(card.id)}
                      className={`cursor-pointer flex flex-col justify-between rounded-xl border p-3 transition ${
                        isSelected
                          ? 'border-gold-400 bg-gold-950/40 ring-2 ring-gold-400/50'
                          : 'border-war-700 bg-war-950/60 hover:border-stone-500'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-2xl">{SYMBOL_ICON[card.symbol] ?? '🃏'}</span>
                        <span className="text-[10px] uppercase font-bold text-stone-400">{SYMBOL_NAME[card.symbol]}</span>
                      </div>
                      <p className="mt-4 text-xs font-bold text-stone-200 capitalize">{territoryName}</p>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="flex items-center justify-between border-t border-war-700 pt-3">
              <span className="text-xs text-stone-400">
                Seleccionadas: <strong className="text-gold-400">{selectedIds.length} / 3</strong>
              </span>
              <button
                disabled={selectedIds.length !== 3 || turn?.phase !== 'reinforcement'}
                onClick={handleTrade}
                className="rounded-xl bg-gold-500 px-4 py-2 text-xs font-bold text-war-950 hover:bg-gold-400 disabled:opacity-30"
              >
                Realizar Canje (+Refuerzos)
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
