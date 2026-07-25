/**
 * Capturas del mapa canónico Modo 50.
 *   node design/tools/capture-canonical.mjs
 * Genera en test-results/ las 8 vistas exigidas por el brief de Arte.
 * No toca el asset: los estados (labels off, selección, ataque) se inyectan
 * en la página de captura, nunca se hornean en el SVG.
 */
import { chromium } from '@playwright/test';
import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { pathToFileURL } from 'url';

const SVG = 'assets/maps/base/map-world-canonical-50-001.svg';
const TMP = 'test-results/.canonical-harness.html';
mkdirSync('test-results', { recursive: true });

const svg = readFileSync(SVG, 'utf8');
writeFileSync(
  TMP,
  `<!doctype html><html><head><meta charset="utf-8"><style>
   html,body{margin:0;padding:0;background:#050d18;height:100%;overflow:hidden}
   svg{display:block;width:100vw;height:100vh}
   body.no-labels #layer-4-overlays{display:none}
   </style></head><body>${svg}</body></html>`
);

const SEL = 'territory-south-america-brazil';
const TGT = 'territory-south-america-argentina';

// `neutral` quita las clases demo p-* igual que hace MapPanel.tsx en runtime:
// las vistas "sin labels" juzgan la lectura del mapamundi, no un reparto ficticio.
const VIEWS = [
  { name: 'canonical-1366x768-labels',        w: 1366, h: 768,  labels: true },
  { name: 'canonical-1366x768-nolabels',      w: 1366, h: 768,  labels: false, neutral: true },
  { name: 'canonical-1920x1080-labels',       w: 1920, h: 1080, labels: true },
  { name: 'canonical-1920x1080-nolabels',     w: 1920, h: 1080, labels: false, neutral: true },
  { name: 'canonical-2560x1440-nolabels',     w: 2560, h: 1440, labels: false, neutral: true },
  { name: 'canonical-3840x2160-nolabels',     w: 3840, h: 2160, labels: false, neutral: true },
  { name: 'canonical-six-players-1920x1080',  w: 1920, h: 1080, labels: false },
  { name: 'canonical-attack-state-1920x1080', w: 1920, h: 1080, labels: true,  attack: true },
];

const browser = await chromium.launch();
for (const v of VIEWS) {
  const page = await browser.newPage({ viewport: { width: v.w, height: v.h } });
  await page.goto(pathToFileURL(TMP).href);
  await page.evaluate(
    ({ labels, attack, neutral, sel, tgt }) => {
      if (!labels) document.body.classList.add('no-labels');
      if (neutral) {
        document.querySelectorAll('#layer-2-playable-territories .territory').forEach((el) => {
          ['p-red', 'p-blue', 'p-green', 'p-yellow', 'p-purple', 'p-cyan'].forEach((c) =>
            el.classList.remove(c)
          );
        });
      }
      if (attack) {
        document.getElementById(sel)?.classList.add('selected');
        document.getElementById(tgt)?.classList.add('attack-target');
        // flecha de ataque: sólo estado visual de la captura, no parte del asset
        const svgEl = document.querySelector('svg');
        const a = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        a.setAttribute('d', 'M 760 1000 C 720 1120, 680 1220, 640 1330');
        a.setAttribute('class', 'vector-arrow');
        a.setAttribute('pointer-events', 'none');
        svgEl.appendChild(a);
      }
    },
    { labels: v.labels, attack: !!v.attack, neutral: !!v.neutral, sel: SEL, tgt: TGT }
  );
  await page.waitForTimeout(250);
  await page.screenshot({ path: `test-results/${v.name}.png` });
  await page.close();
  console.log('captura', v.name, `${v.w}x${v.h}`);
}
await browser.close();
