/** Detecta si el navegador dibuja emoji a color (si no, la UI usa texto).
 * Dibuja un emoji en un canvas y busca algún píxel no monocromo. */
let cached: boolean | null = null;

export function emojiSupported(): boolean {
  if (cached !== null) return cached;
  try {
    const canvas = document.createElement('canvas');
    canvas.width = 20;
    canvas.height = 20;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return (cached = false);
    ctx.textBaseline = 'top';
    ctx.font = '16px sans-serif';
    ctx.fillText('🔥', 0, 0);
    const data = ctx.getImageData(0, 0, 20, 20).data;
    for (let i = 0; i < data.length; i += 4) {
      const [r, g, b, a] = [data[i], data[i + 1], data[i + 2], data[i + 3]];
      // un emoji a color tiene píxeles con canales desiguales; un tofu/cuadro
      // renderiza monocromo (r=g=b) o directamente vacío
      if (a > 0 && (Math.abs(r - g) > 16 || Math.abs(g - b) > 16)) {
        return (cached = true);
      }
    }
    return (cached = false);
  } catch {
    return (cached = false);
  }
}
