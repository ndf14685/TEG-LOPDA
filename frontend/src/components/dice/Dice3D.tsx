import { useEffect, useState } from 'react';

export interface Dice3DProps {
  value: number;
  variant?: 'attacker' | 'defender';
  isRolling?: boolean;
  isWinner?: boolean;
  isLoser?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const ROTATIONS: Record<number, { x: number; y: number }> = {
  1: { x: 0, y: 0 },
  2: { x: 0, y: 180 },
  3: { x: 0, y: -90 },
  4: { x: 0, y: 90 },
  5: { x: -90, y: 0 },
  6: { x: 90, y: 0 },
};

// Renderizado de Pips (puntos del dado) para cada cara 1..6
const PIP_POSITIONS: Record<number, number[]> = {
  1: [4], // centro
  2: [0, 8], // esquinas sup-izq, inf-der
  3: [0, 4, 8], // diagonal
  4: [0, 2, 6, 8], // 4 esquinas
  5: [0, 2, 4, 6, 8], // 4 esquinas + centro
  6: [0, 2, 3, 5, 6, 8], // 2 columnas de 3
};

function RenderFace({ faceNumber, variant }: { faceNumber: number; variant: 'attacker' | 'defender' }) {
  const pips = PIP_POSITIONS[faceNumber] ?? [];
  const pipBg = variant === 'attacker' ? 'bg-amber-100 shadow-[0_0_6px_rgba(251,191,36,0.8)]' : 'bg-sky-100 shadow-[0_0_6px_rgba(56,189,248,0.8)]';

  return (
    <div className="grid h-full w-full grid-cols-3 grid-rows-3 p-1.5">
      {Array.from({ length: 9 }).map((_, idx) => (
        <div key={idx} className="flex items-center justify-center">
          {pips.includes(idx) && <div className={`h-2.5 w-2.5 rounded-full ${pipBg}`} />}
        </div>
      ))}
    </div>
  );
}

export function Dice3D({
  value,
  variant = 'attacker',
  isRolling = false,
  isWinner = false,
  isLoser = false,
  size = 'md',
}: Dice3DProps) {
  const [animating, setAnimating] = useState(isRolling);

  useEffect(() => {
    if (isRolling) {
      setAnimating(true);
    } else {
      const timer = setTimeout(() => setAnimating(false), 300);
      return () => clearTimeout(timer);
    }
  }, [isRolling]);

  const rot = ROTATIONS[value] ?? ROTATIONS[1];
  const sizePx = size === 'sm' ? 44 : size === 'lg' ? 72 : 56;
  const halfPx = sizePx / 2;

  const bgStyle =
    variant === 'attacker'
      ? 'bg-gradient-to-br from-red-800 via-amber-900 to-red-950 border-amber-500/80 text-amber-100'
      : 'bg-gradient-to-br from-sky-900 via-slate-900 to-indigo-950 border-sky-400/80 text-sky-100';

  const glowStyle = isWinner
    ? 'ring-4 ring-emerald-400 shadow-[0_0_20px_rgba(52,211,153,0.9)] scale-105'
    : isLoser
      ? 'opacity-40 grayscale contrast-125'
      : '';

  return (
    <div
      className={`relative transition-all duration-300 ${glowStyle}`}
      style={{
        width: `${sizePx}px`,
        height: `${sizePx}px`,
        perspective: '600px',
      }}
    >
      <div
        className={`h-full w-full transition-transform duration-500 ease-out ${animating ? 'animate-bounce' : ''}`}
        style={{
          transformStyle: 'preserve-3d',
          transform: animating
            ? `rotateX(${Math.random() * 720}deg) rotateY(${Math.random() * 720}deg)`
            : `rotateX(${rot.x}deg) rotateY(${rot.y}deg)`,
        }}
      >
        {/* CARA 1: Front */}
        <div
          className={`absolute inset-0 rounded-xl border-2 shadow-lg ${bgStyle}`}
          style={{ transform: `rotateY(0deg) translateZ(${halfPx}px)` }}
        >
          <RenderFace faceNumber={1} variant={variant} />
        </div>
        {/* CARA 2: Back */}
        <div
          className={`absolute inset-0 rounded-xl border-2 shadow-lg ${bgStyle}`}
          style={{ transform: `rotateY(180deg) translateZ(${halfPx}px)` }}
        >
          <RenderFace faceNumber={2} variant={variant} />
        </div>
        {/* CARA 3: Right */}
        <div
          className={`absolute inset-0 rounded-xl border-2 shadow-lg ${bgStyle}`}
          style={{ transform: `rotateY(90deg) translateZ(${halfPx}px)` }}
        >
          <RenderFace faceNumber={3} variant={variant} />
        </div>
        {/* CARA 4: Left */}
        <div
          className={`absolute inset-0 rounded-xl border-2 shadow-lg ${bgStyle}`}
          style={{ transform: `rotateY(-90deg) translateZ(${halfPx}px)` }}
        >
          <RenderFace faceNumber={4} variant={variant} />
        </div>
        {/* CARA 5: Top */}
        <div
          className={`absolute inset-0 rounded-xl border-2 shadow-lg ${bgStyle}`}
          style={{ transform: `rotateX(90deg) translateZ(${halfPx}px)` }}
        >
          <RenderFace faceNumber={5} variant={variant} />
        </div>
        {/* CARA 6: Bottom */}
        <div
          className={`absolute inset-0 rounded-xl border-2 shadow-lg ${bgStyle}`}
          style={{ transform: `rotateX(-90deg) translateZ(${halfPx}px)` }}
        >
          <RenderFace faceNumber={6} variant={variant} />
        </div>
      </div>
    </div>
  );
}
