import { useState } from 'react';
import { useGameStore } from '../../state/gameStore';

export function SecretObjectiveModal() {
  const objective = useGameStore((s) => s.secretObjective);
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsVisible(!isVisible)}
        className="flex items-center gap-1.5 rounded-lg border border-purple-500/40 bg-purple-950/40 px-3 py-1.5 text-xs font-bold text-purple-300 hover:bg-purple-900/50 shadow-md"
      >
        <span>{isVisible ? 'Ocultar objetivo' : 'Objetivo secreto'}</span>
      </button>

      {isVisible && (
        <div className="absolute top-10 right-0 z-30 w-72 rounded-xl border border-purple-500/50 bg-war-950 p-4 shadow-2xl backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-purple-900/60 pb-2">
            <span className="text-xs font-bold text-purple-300">🕵️ TU OBJETIVO SECRETO</span>
            <button onClick={() => setIsVisible(false)} className="text-xs text-stone-400 hover:text-white font-bold">
              ✕
            </button>
          </div>
          {objective ? (
            <>
              <h4 className="mt-2 text-sm font-bold text-gold-400">{objective.title}</h4>
              <p className="mt-1 text-xs text-stone-300 leading-relaxed">{objective.description}</p>
            </>
          ) : (
            <p className="mt-2 text-xs text-stone-400">
              Tu objetivo se revela al iniciar la partida.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
