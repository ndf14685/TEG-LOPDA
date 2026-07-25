/**
 * Capturas del mapa canónico Modo 50.
 *   node design/tools/capture-canonical.mjs <svg> <prefijo>
 * Los estados (labels off, territorios neutros, selección, ataque) se inyectan
 * en la página de captura: nunca se hornean en el asset.
 */
import { chromium } from '@playwright/test';
import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { pathToFileURL } from 'url';

const SVG = process.argv[2] ?? 'assets/maps/base/map-world-canonical-50-002.svg';
const PREFIX = process.argv[3] ?? 'canonical-v2';
mkdirSync('test-results', { recursive: true });

const TMP = `test-results/.${PREFIX}-harness.html`;
writeFileSync(
  TMP,
  `<!doctype html><html><head><meta charset="utf-8"><style>
   html,body{margin:0;padding:0;background:#050d18;height:100%;overflow:hidden}
   svg{display:block;width:100vw;height:100vh}
   body.no-labels #layer-4-overlays{display:none}
   </style></head><body>${readFileSync(SVG, 'utf8')}</body></html>`
);

// par declarado adyacente por el backend y que además se tocan en el mapa
const SEL = 'territory-south-america-brazil';
const TGT = 'territory-south-america-bolivia';
const PLAYERS = ['p-red', 'p-blue', 'p-green', 'p-yellow', 'p-purple', 'p-cyan'];

const VIEWS = [
  { name: `${PREFIX}-1366x768-labels`,    w: 1366, h: 768,  labels: true,  players: true },
  { name: `${PREFIX}-1366x768-nolabels`,  w: 1366, h: 768,  labels: false },
  { name: `${PREFIX}-1920x1080-labels`,   w: 1920, h: 1080, labels: true,  players: true },
  { name: `${PREFIX}-1920x1080-nolabels`, w: 1920, h: 1080, labels: false },
  { name: `${PREFIX}-2560x1440-nolabels`, w: 2560, h: 1440, labels: false },
  { name: `${PREFIX}-3840x2160-nolabels`, w: 3840, h: 2160, labels: false },
  { name: `${PREFIX}-six-players`,        w: 1920, h: 1080, labels: true,  players: true },
  { name: `${PREFIX}-attack-state`,       w: 1920, h: 1080, labels: true,  players: true, attack: true },
];

const browser = await chromium.launch();
for (const v of VIEWS) {
  const page = await browser.newPage({ viewport: { width: v.w, height: v.h } });
  await page.goto(pathToFileURL(TMP).href);
  await page.evaluate(
    ({ labels, players, attack, sel, tgt, colors }) => {
      if (!labels) document.body.classList.add('no-labels');
      const terrs = [...document.querySelectorAll('#layer-2-playable-territories .territory')];
      if (players) terrs.forEach((el, i) => el.classList.add(colors[i % colors.length]));
      if (attack) {
        const a = document.getElementById(sel);
        const b = document.getElementById(tgt);
        a?.classList.add('selected');
        b?.classList.add('attack-target');
        const c = (el) => {
          const bb = el.getBBox();
          return [bb.x + bb.width / 2, bb.y + bb.height / 2];
        };
        if (a && b) {
          const [x1, y1] = c(a);
          const [x2, y2] = c(b);
          const arrow = document.createElementNS('http://www.w3.org/2000/svg', 'path');
          arrow.setAttribute('d', `M ${x1} ${y1} L ${x2} ${y2}`);
          arrow.setAttribute('class', 'vector-arrow');
          arrow.setAttribute('pointer-events', 'none');
          document.querySelector('svg').appendChild(arrow);
        }
      }
    },
    { labels: v.labels, players: !!v.players, attack: !!v.attack, sel: SEL, tgt: TGT, colors: PLAYERS }
  );
  await page.waitForTimeout(250);
  await page.screenshot({ path: `test-results/${v.name}.png` });
  await page.close();
  console.log('captura', v.name, `${v.w}x${v.h}`);
}
await browser.close();
