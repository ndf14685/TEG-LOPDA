// Captura genérica de una página local a PNG. Uso: node shot.mjs <html> <out> <w> <h>
import { chromium } from '@playwright/test';
import { pathToFileURL } from 'url';
const [html, out, w, h] = process.argv.slice(2);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: +w, height: +h } });
await page.goto(pathToFileURL(html).href);
await page.waitForTimeout(250);
await page.screenshot({ path: out });
await browser.close();
console.log('captura', out, `${w}x${h}`);
