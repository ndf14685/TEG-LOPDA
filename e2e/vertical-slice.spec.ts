import { test, expect } from '@playwright/test';

/**
 * Vertical slice completo con DOS contextos de navegador independientes:
 * admin crea partida y link → jugador entra por link → ambos en lobby →
 * jugador listo → admin inicia → tablero visible → comentario IA en ambos.
 */
test('vertical slice: crear, invitar, lobby, iniciar, comentarista IA', async ({ browser }) => {
  const adminCtx = await browser.newContext();
  const playerCtx = await browser.newContext();
  const admin = await adminCtx.newPage();
  const player = await playerCtx.newPage();

  // 1. El administrador crea una partida
  await admin.goto('/');
  await expect(admin.getByTestId('server-status')).toContainText('servidor operativo');
  await admin.getByTestId('admin-name').fill('Néstor');
  await admin.getByTestId('admin-nickname').fill('Nessi');
  await admin.getByTestId('create-game').click();
  await expect(admin.getByText('Cuartel general')).toBeVisible();

  // 2. Genera un link personalizado para otro jugador
  await admin.getByTestId('new-player-name').fill('Darío');
  await admin.getByTestId('new-player-nickname').fill('Daro');
  await admin.getByTestId('create-player').click();
  await expect(admin.getByTestId('link-row-Daro')).toBeVisible();

  // extraemos el link real desde el portapapeles del contexto admin
  await adminCtx.grantPermissions(['clipboard-read', 'clipboard-write']);
  await admin.getByTestId('copy-link-Daro').click();
  const joinUrl = await admin.evaluate(() => navigator.clipboard.readText());
  expect(joinUrl).toContain('/join/');

  // 3. Otro navegador entra con ese link
  await player.goto(joinUrl);
  await expect(player.getByTestId('identity-card')).toBeVisible();
  await expect(player.getByTestId('identity-card')).toContainText('Darío');
  await player.getByTestId('nickname-input').fill('Daro El Traidor');
  await player.getByTestId('enter-lobby').click();

  // 4. Ambos aparecen en el lobby
  await admin.getByTestId('go-lobby').click();
  await expect(admin.getByTestId('player-card-Nessi')).toBeVisible();
  await expect(admin.getByTestId('player-card-Daro El Traidor')).toBeVisible();
  await expect(player.getByTestId('player-card-Nessi')).toBeVisible();
  await expect(player.getByTestId('player-card-Daro El Traidor')).toBeVisible();

  // 5. El segundo jugador marca "listo" y el admin lo ve
  await player.getByTestId('ready-button').click();
  await expect(admin.getByTestId('start-game')).toContainText('1 listos');

  // 6. El administrador inicia (countdown en ambos)
  await admin.getByTestId('start-game').click();
  await expect(admin.getByTestId('countdown')).toBeVisible();
  await expect(player.getByTestId('countdown')).toBeVisible();

  // 7. Se muestra el tablero inicial en ambos navegadores
  await expect(admin.getByTestId('game-board')).toBeVisible({ timeout: 15_000 });
  await expect(player.getByTestId('game-board')).toBeVisible({ timeout: 15_000 });
  await expect(admin.getByTestId('territory-america-sur.argentina')).toBeVisible();

  // 8-9. El backend emite el comentario mock y el comentarista bardea en ambos
  await expect(admin.getByTestId('ai-comment')).toBeVisible({ timeout: 15_000 });
  await expect(player.getByTestId('ai-comment')).toBeVisible({ timeout: 15_000 });

  // 10. Ambos navegadores ven el mismo estado (mismo texto de comentario, misma fase)
  const adminComment = await admin.getByTestId('ai-comment').locator('p').textContent();
  const playerComment = await player.getByTestId('ai-comment').locator('p').textContent();
  expect(adminComment).toBeTruthy();
  expect(playerComment).toBe(adminComment);
  await expect(admin.getByTestId('turn-panel')).toContainText('Fase: Refuerzos');
  await expect(player.getByTestId('turn-panel')).toContainText('Fase: Refuerzos');

  // capturas del estado final
  await admin.screenshot({ path: 'test-results/slice-admin-board.png', fullPage: true });
  await player.screenshot({ path: 'test-results/slice-player-board.png', fullPage: true });

  await adminCtx.close();
  await playerCtx.close();
});

test('link revocado muestra error claro', async ({ browser }) => {
  const adminCtx = await browser.newContext();
  const admin = await adminCtx.newPage();

  await admin.goto('/');
  await admin.getByTestId('admin-name').fill('Admin');
  await admin.getByTestId('admin-nickname').fill('ElJefe');
  await admin.getByTestId('create-game').click();
  await admin.getByTestId('new-player-name').fill('Víctima');
  await admin.getByTestId('new-player-nickname').fill('Banned');
  await admin.getByTestId('create-player').click();

  await adminCtx.grantPermissions(['clipboard-read', 'clipboard-write']);
  await admin.getByTestId('copy-link-Banned').click();
  const joinUrl = await admin.evaluate(() => navigator.clipboard.readText());

  await admin.getByRole('button', { name: '🚫 revocar' }).click();

  const playerCtx = await browser.newContext();
  const player = await playerCtx.newPage();
  await player.goto(joinUrl);
  await expect(player.getByTestId('join-error')).toContainText('revocó');

  await adminCtx.close();
  await playerCtx.close();
});
