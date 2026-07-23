import { useState } from 'react';

/** Botón "📜 Cómo se juega": despliega un papiro con las reglas del turno. */
export function HowToPlayModal() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 rounded-lg border border-amber-500/40 bg-amber-950/40 px-3 py-1.5 text-xs font-bold text-amber-300 shadow-md hover:bg-amber-900/50"
        data-testid="how-to-play"
      >
        <span>📜 Cómo se juega</span>
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          onClick={() => setOpen(false)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-xl border-4 border-amber-800/70 bg-gradient-to-b from-amber-100 to-amber-200 p-6 font-serif text-stone-900 shadow-2xl"
            style={{ backgroundImage: 'radial-gradient(ellipse at top, #fef3c7, #fde68a 70%, #d9b365)' }}
          >
            <div className="mb-3 flex items-start justify-between border-b-2 border-amber-800/40 pb-2">
              <h2 className="text-xl font-black tracking-wide">📜 Manual de Guerra</h2>
              <button
                onClick={() => setOpen(false)}
                className="rounded px-2 text-lg font-bold text-amber-900 hover:bg-amber-300"
                aria-label="Cerrar"
              >
                ✕
              </button>
            </div>

            <p className="mb-3 text-sm italic">
              Cada turno tiene <strong>3 fases en orden</strong> — la barra sobre el mapa
              marca en cuál estás. Solo el jugador de turno puede actuar.
            </p>

            <h3 className="mb-1 font-black">🪖 Fase 1 — Refuerzos</h3>
            <p className="mb-3 text-sm">
              Tenés ejércitos nuevos para colocar (mirá el contador <em>Disponibles</em>).
              <strong> Hacé click sobre tus países</strong> en el mapa: cada click suma 1 ejército.
              Al llegar a 0 pasás solo a la fase de ataque. Consejo: reforzá las fronteras
              con enemigos, no los países del fondo.
            </p>

            <h3 className="mb-1 font-black">⚔️ Fase 2 — Ataque</h3>
            <ol className="mb-3 list-decimal pl-5 text-sm">
              <li>Click en un país <strong>tuyo</strong> con <strong>2+ ejércitos</strong> (origen).</li>
              <li>Click en un país <strong>enemigo vecino</strong> (frontera directa).</li>
              <li>Apretá <strong>"⚔️ Atacar"</strong> en el panel derecho.</li>
            </ol>
            <p className="mb-3 text-sm">
              Los dados los tira el servidor: hasta 3 de ataque según tus ejércitos.
              <strong> El empate lo gana el defensor.</strong> Si el defensor queda en 0,
              conquistás el país y tus tropas avanzan. Podés atacar todas las veces que
              quieras; cuando termines, botón <em>"Pasar a Reagrupar"</em>.
            </p>

            <h3 className="mb-1 font-black">🛡️ Fase 3 — Reagrupar (opcional)</h3>
            <p className="mb-3 text-sm">
              Mové ejércitos entre países tuyos: click en el origen → click en otro país
              tuyo → elegí cuántos → <strong>"🛡️ Mover"</strong>. Siempre queda al menos 1
              en el origen. Después, <em>"Fin de Turno"</em> y juega el siguiente.
            </p>

            <div className="border-t-2 border-amber-800/40 pt-2 text-sm">
              <p className="mb-1 font-black">Reglas del imperio</p>
              <ul className="list-disc pl-5">
                <li>Refuerzos por turno: la mitad de tus países (mínimo 3) + bonus por continente completo.</li>
                <li>El que pierde su último país queda eliminado.</li>
                <li>Gana el último que quede en pie. Sin llorar en el chat (se puede, pero queda registrado).</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
