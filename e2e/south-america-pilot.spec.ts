import { test, expect, type Page, type APIRequestContext } from '@playwright/test';

const ADMIN = { 'X-Admin-Token': 'dev-admin' };
const API = 'http://localhost:8124';
const SA = 'territory-south-america-';

/**
 * P0 Mapa — piloto América del Sur en el mapa productivo (modo 50).
 * Partida real contra el backend: valida IDs intactos, capa de hitboxes,
 * labels/tropas, propiedad, selección, atacable y ataque en ejecución.
 * Genera las 6 capturas requeridas por el brief.
 */

async function createGame50(request: APIRequestContext) {
  const game = await (
    await request.post(`${API}/api/admin/games`, {
      headers: ADMIN,
      data: { name: 'piloto-sa', config: { game_mode: 'classic_50', commentator_enabled: false } },
    })
  ).json();
  const invite = async (nickname: string, color: string, role = 'player') =>
    (
      await request.post(`${API}/api/admin/games/${game.game.id}/players`, {
        headers: ADMIN,
        data: { nickname, color, role },
      })
    ).json();
  const inv1 = await invite('Nessi', 'red');
  const inv2 = await invite('Daro', 'blue');
  // cuatro bots con colores distintos: valida la propiedad con SEIS colores
  await invite('BotVerde', 'green', 'ai_player');
  await invite('BotOro', 'yellow', 'ai_player');
  await invite('BotVioleta', 'purple', 'ai_player');
  await invite('BotCian', 'cyan', 'ai_player');
  return { game: game.game, inv1, inv2 };
}

async function joinAndReady(page: Page, joinUrl: string) {
  await page.goto(joinUrl.replace(/^https?:\/\/[^/]+/, ''));
  await page.getByTestId('enter-lobby').click();
  await page.getByTestId('ready-button').click();
}

/** Click sobre un territorio a través de su hitbox si existe (piloto SA). */
async function clickTerritory(page: Page, pathLocator: ReturnType<Page['locator']>) {
  const id = await pathLocator.first().getAttribute('id');
  const hb = page.locator(`path.territory-hitbox[data-territory="${id}"]`);
  // force: los bordes encastados se solapan unos píxeles y el hitbox vecino
  // puede cubrir el centro geométrico; el destino del test es determinista
  if (await hb.count()) await hb.first().click({ force: true });
  else await pathLocator.first().click({ force: true });
}

async function placeAllViaRadial(page: Page, preferSA: boolean) {
  const saFrontier = page.locator(`path.territory.frontier[id^="${SA}"]`);
  const anyFrontier = page.locator('path.territory.frontier[data-mine="true"]');
  const anyMine = page.locator('path.territory[data-mine="true"]');
  if (preferSA && (await saFrontier.count())) await clickTerritory(page, saFrontier);
  else if (await anyFrontier.count()) await clickTerritory(page, anyFrontier);
  else await clickTerritory(page, anyMine);
  const max = page.locator('.radial-menu button', { hasText: 'MÁX' });
  if (await max.count()) await max.first().click();
  else await page.locator('.radial-menu button', { hasText: '+1' }).first().click();
  await page.waitForTimeout(250);
}

test('piloto SA: geometría real integrada en partida productiva modo 50', async ({ browser, request }) => {
  const { game, inv1, inv2 } = await createGame50(request);

  const ctx1 = await browser.newContext();
  const ctx2 = await browser.newContext();
  const p1 = await ctx1.newPage();
  const p2 = await ctx2.newPage();
  await joinAndReady(p1, inv1.join_url);
  await joinAndReady(p2, inv2.join_url);

  const start = await request.post(`${API}/api/admin/games/${game.id}/start`, { headers: ADMIN });
  expect(start.ok()).toBeTruthy();

  await expect(p1.getByTestId('game-board')).toBeVisible({ timeout: 15_000 });
  await expect(p2.getByTestId('game-board')).toBeVisible({ timeout: 15_000 });

  // IDs del piloto presentes con geometría nueva + hitboxes separados
  for (const country of ['argentina', 'brazil', 'bolivia', 'uruguay', 'venezuela']) {
    await expect(p1.locator(`path#${SA}${country}.territory`)).toBeAttached();
    await expect(p1.locator(`path.territory-hitbox[data-territory="${SA}${country}"]`)).toBeAttached();
  }

  // colocación 5+3 priorizando fronteras sudamericanas
  await expect(p1.getByTestId('tribune-turn-box')).toContainText('COLOCACIÓN INICIAL', { timeout: 10_000 });
  for (const round of [0, 1]) {
    await placeAllViaRadial(p1, true);
    await placeAllViaRadial(p2, true);
    if (round === 0) {
      await expect(p1.getByTestId('tribune-turn-box')).toContainText('(3 tropas)', { timeout: 10_000 });
    }
  }
  await expect(p1.getByTestId('hud-phase')).toContainText('REFUERZOS', { timeout: 10_000 });

  // jugador activo
  let active = p1;
  await expect
    .poll(async () => {
      const a = (await p1.getByTestId('tribune-turn-box').textContent()) ?? '';
      const b = (await p2.getByTestId('tribune-turn-box').textContent()) ?? '';
      if (a.includes('ES TU TURNO')) { active = p1; return true; }
      if (b.includes('ES TU TURNO')) { active = p2; return true; }
      return false;
    }, { timeout: 45_000 })
    .toBe(true);

  // refuerzos a una frontera SA y a fase de ataque
  await placeAllViaRadial(active, true);
  await expect(active.getByTestId('hud-phase')).toContainText('ATAQUE', { timeout: 10_000 });
  await active.waitForTimeout(3200); // pasa el banner de turno

  // ── capturas normales en 4 resoluciones (base geográfica visible) ──
  // incluye QHD 2560x1440 y 4K 3840x2160 para validar responsive
  for (const [w, h] of [[1366, 768], [1920, 1080], [2560, 1440], [3840, 2160]] as const) {
    await active.setViewportSize({ width: w, height: h });
    await active.waitForTimeout(200);
    await active.screenshot({ path: `test-results/sa-pilot-${w}x${h}.png` });
  }
  await active.setViewportSize({ width: 1920, height: 1080 });

  // ── captura 3: sin labels (toggle Aa) ──
  await active.getByTestId('labels-toggle').click();
  await active.screenshot({ path: 'test-results/sa-pilot-no-labels.png' });
  await active.getByTestId('labels-toggle').click();

  // ── captura 4: estado seleccionado (origen elegido, preferentemente SA) ──
  const saAttack = active.locator(`path.territory.can-attack[id^="${SA}"]`);
  const source = (await saAttack.count()) ? saAttack : active.locator('path.territory.can-attack');
  await clickTerritory(active, source);
  await active.locator('.radial-menu button', { hasText: 'ATACAR' }).click();
  await expect(active.locator('path.territory.attack-source')).toBeAttached();
  await active.screenshot({ path: 'test-results/sa-pilot-selected.png' });

  // ── captura 5: estado atacable (objetivos resaltados) ──
  await expect(active.locator('path.territory.attackable').first()).toBeAttached();
  await active.screenshot({ path: 'test-results/sa-pilot-attackable.png' });

  // ── captura 6: ataque en ejecución (Arena abierta) ──
  await clickTerritory(active, active.locator('path.territory.attackable'));
  await expect(active.getByTestId('combat-arena')).toBeVisible({ timeout: 10_000 });
  await active.screenshot({ path: 'test-results/sa-pilot-executing.png' });
  // si la conquista ganó la partida al instante (objetivo cumplido), el
  // modal de fin de partida reemplaza a la Arena: ambos finales son válidos
  if (await active.getByTestId('post-game-modal').count()) {
    await expect(active.getByTestId('post-game-modal')).toBeVisible();
  } else {
    await active.getByTestId('stop-attack').click();
    await expect(active.getByTestId('combat-arena')).toHaveCount(0);
  }

  await ctx1.close();
  await ctx2.close();
});
