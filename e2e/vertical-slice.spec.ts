import { test, expect, type Page } from '@playwright/test';

const ADMIN_TOKEN = 'dev-admin';

/** Colocación con el menú radial: click en país propio → botón MÁX. */
async function placeAllViaRadial(page: Page) {
  await page.locator('path.territory[data-mine="true"]').first().click();
  const max = page.locator('.radial-menu button', { hasText: 'MÁX' });
  const plusOne = page.locator('.radial-menu button', { hasText: '+1' });
  if (await max.count()) await max.first().click();
  else await plusOne.first().click();
  await page.waitForTimeout(250);
}

/** Colocación inicial canónica 5+3 en ambas pantallas vía menú radial. */
async function completePlacement(admin: Page, player: Page) {
  await expect(admin.getByTestId('tribune-turn-box')).toContainText('COLOCACIÓN INICIAL', { timeout: 10_000 });
  await placeAllViaRadial(admin);
  await placeAllViaRadial(player);
  // segunda ronda (3 tropas): el box lo anuncia
  await expect(admin.getByTestId('tribune-turn-box')).toContainText('(3 tropas)', { timeout: 10_000 });
  await placeAllViaRadial(admin);
  await placeAllViaRadial(player);
  // al terminar arranca el primer turno: el HUD muestra la fase
  await expect(admin.getByTestId('hud-phase')).toContainText('REFUERZOS', { timeout: 10_000 });
}

async function createGameAsAdmin(admin: Page, nickname: string) {
  await admin.goto('/');
  await expect(admin.getByTestId('server-status')).toContainText('servidor operativo');
  await admin.getByTestId('admin-token').fill(ADMIN_TOKEN);
  await admin.getByTestId('admin-nickname').fill(nickname);
  await admin.getByTestId('create-game').click();
  await expect(admin.getByText('Cuartel general')).toBeVisible();
}

/**
 * Slice real multi-contexto contra el backend FastAPI: crear → invitar →
 * lobby → iniciar → colocación por menú radial → primer turno sincronizado
 * en ambos navegadores → refuerzos y cambio de fase visibles para todos.
 */
test('slice real: lobby, colocación radial, turno y fases sincronizadas', async ({ browser }) => {
  const adminCtx = await browser.newContext();
  const playerCtx = await browser.newContext();
  const admin = await adminCtx.newPage();
  const player = await playerCtx.newPage();

  // 1-2. partida + link personalizado
  await createGameAsAdmin(admin, 'Nessi');
  await admin.getByTestId('new-player-nickname').fill('Daro');
  await admin.getByTestId('create-player').click();
  await expect(admin.getByTestId('link-row-Daro')).toBeVisible();

  await adminCtx.grantPermissions(['clipboard-read', 'clipboard-write']);
  await admin.getByTestId('copy-link-Daro').click();
  const joinUrl = await admin.evaluate(() => navigator.clipboard.readText());
  expect(new URL(joinUrl).origin).toBe(new URL(admin.url()).origin);
  expect(joinUrl).toContain('/join/');

  // 3. otro navegador entra con ese link y confirma su apodo
  await player.goto(joinUrl);
  await expect(player.getByTestId('identity-card')).toBeVisible();
  await expect(player.getByTestId('identity-card')).toContainText('Daro');
  await player.getByTestId('nickname-input').fill('Daro El Traidor');
  await player.getByTestId('enter-lobby').click();

  // 4. ambos en el lobby
  await admin.getByTestId('go-lobby').click();
  await expect(admin.getByTestId('player-card-Nessi')).toBeVisible();
  await expect(admin.getByTestId('player-card-Daro El Traidor')).toBeVisible();
  await expect(player.getByTestId('player-card-Nessi')).toBeVisible();
  await expect(player.getByTestId('player-card-Daro El Traidor')).toBeVisible();

  // 5. el jugador marca listo y el admin lo ve
  await player.getByTestId('ready-button').click();
  await expect(admin.getByTestId('start-game')).toContainText('1 listos');
  await expect(admin.getByTestId('ready-Daro El Traidor')).not.toHaveClass(/opacity-30/);

  // 6. el admin inicia: countdown en ambos
  await admin.getByTestId('start-game').click();
  await expect(admin.getByTestId('countdown')).toBeVisible();
  await expect(player.getByTestId('countdown')).toBeVisible();

  // 7. tablero con HUD y Tribuna en ambos
  await expect(admin.getByTestId('game-board')).toBeVisible({ timeout: 15_000 });
  await expect(player.getByTestId('game-board')).toBeVisible({ timeout: 15_000 });
  await expect(admin.getByTestId('map-panel')).toBeVisible();
  await expect(admin.getByTestId('top-hud')).toBeVisible();
  await expect(admin.getByTestId('tribune-panel')).toBeVisible();

  // 8. el relator comenta en ambos navegadores (mock determinista)
  await expect(admin.getByTestId('ai-comment')).toBeVisible({ timeout: 20_000 });
  await expect(player.getByTestId('ai-comment')).toBeVisible({ timeout: 20_000 });

  // 9. colocación inicial 5+3 con el menú radial en ambas pantallas
  await completePlacement(admin, player);

  // 10. claridad de turno: los DOS saben quién juega y qué fase es
  await expect(player.getByTestId('hud-phase')).toContainText('REFUERZOS', { timeout: 10_000 });
  // el sorteo es aleatorio: encontrar al activo esperando su "ES TU TURNO"
  let active = admin;
  let passive = player;
  await expect
    .poll(async () => {
      const a = (await admin.getByTestId('tribune-turn-box').textContent()) ?? '';
      const p = (await player.getByTestId('tribune-turn-box').textContent()) ?? '';
      if (a.includes('ES TU TURNO')) { active = admin; passive = player; return true; }
      if (p.includes('ES TU TURNO')) { active = player; passive = admin; return true; }
      return false;
    }, { timeout: 10_000 })
    .toBe(true);
  await expect(passive.getByTestId('tribune-turn-box')).toContainText('TURNO DE');

  // 11. el jugador activo coloca TODOS sus refuerzos vía radial y pasa a ataque
  await placeAllViaRadial(active);
  await expect(active.getByTestId('hud-phase')).toContainText('ATAQUE', { timeout: 10_000 });
  await expect(passive.getByTestId('hud-phase')).toContainText('ATAQUE', { timeout: 10_000 });

  // 12. capturas LIMPIAS del turno (sin modales) en dos resoluciones
  await admin.waitForTimeout(3200); // deja pasar el banner de turno
  await admin.setViewportSize({ width: 1366, height: 768 });
  await admin.screenshot({ path: 'test-results/product-1366x768-turn.png' });
  await admin.setViewportSize({ width: 1920, height: 1080 });
  await admin.screenshot({ path: 'test-results/product-1920x1080-turn.png' });
  await player.screenshot({ path: 'test-results/product-player-view.png' });

  // 13. combate real: radial → ATACAR → objetivo resaltado → Arena en AMBOS
  await active.locator('path.territory.can-attack').first().click();
  await active.locator('.radial-menu button', { hasText: 'ATACAR' }).click();
  await active.locator('path.territory.attackable').first().click();
  await expect(active.getByTestId('combat-arena')).toBeVisible({ timeout: 10_000 });
  await expect(active.getByTestId('battle-summary')).toContainText('RESUMEN ACUMULADO');
  await expect(passive.getByTestId('combat-arena')).toBeVisible({ timeout: 10_000 });
  await active.screenshot({ path: 'test-results/product-combat-arena.png' });
  await active.getByTestId('stop-attack').click();
  await expect(active.getByTestId('combat-arena')).toHaveCount(0);

  // 14. el mercado de espectadores se declara BLOQUEADO sin controles activos
  await expect(active.getByTestId('spectator-market')).toContainText('BLOQUEADO');

  await adminCtx.close();
  await playerCtx.close();
});

test('link expulsado/revocado muestra error claro', async ({ browser }) => {
  const adminCtx = await browser.newContext();
  const admin = await adminCtx.newPage();

  await createGameAsAdmin(admin, 'ElJefe');
  await admin.getByTestId('new-player-nickname').fill('Banned');
  await admin.getByTestId('create-player').click();

  await adminCtx.grantPermissions(['clipboard-read', 'clipboard-write']);
  await admin.getByTestId('copy-link-Banned').click();
  const joinUrl = await admin.evaluate(() => navigator.clipboard.readText());

  await admin.getByTestId('link-row-Banned').getByRole('button', { name: '🚫 expulsar' }).click();

  const playerCtx = await browser.newContext();
  const player = await playerCtx.newPage();
  await player.goto(joinUrl);
  await expect(player.getByTestId('join-error')).toContainText('no corresponde a ninguna partida');

  await adminCtx.close();
  await playerCtx.close();
});
