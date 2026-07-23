import { test, expect, type Page } from '@playwright/test';

const ADMIN_TOKEN = 'dev-admin';

async function createGameAsAdmin(admin: Page, nickname: string) {
  await admin.goto('/');
  await expect(admin.getByTestId('server-status')).toContainText('servidor operativo');
  await admin.getByTestId('admin-token').fill(ADMIN_TOKEN);
  await admin.getByTestId('admin-nickname').fill(nickname);
  await admin.getByTestId('create-game').click();
  await expect(admin.getByText('Cuartel general')).toBeVisible();
}

/**
 * Vertical slice contra el backend FastAPI real, con DOS contextos de
 * navegador independientes: admin crea partida y link → jugador entra por
 * link → ambos en lobby → listo → inicio → tablero → comentario IA en ambos
 * → una tirada de dados visible en ambos.
 */
test('slice real: crear, invitar, lobby, iniciar, IA y dados sincronizados', async ({ browser }) => {
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

  // 7. tablero inicial en ambos
  await expect(admin.getByTestId('game-board')).toBeVisible({ timeout: 15_000 });
  await expect(player.getByTestId('game-board')).toBeVisible({ timeout: 15_000 });
  await expect(admin.getByTestId('map-panel')).toBeVisible();

  // 8-9. el backend emite el comentario (mock commentator, game.started) y ambos lo ven
  await expect(admin.getByTestId('ai-comment')).toBeVisible({ timeout: 20_000 });
  await expect(player.getByTestId('ai-comment')).toBeVisible({ timeout: 20_000 });
  const adminComment = await admin.getByTestId('ai-comment').locator('p').textContent();
  const playerComment = await player.getByTestId('ai-comment').locator('p').textContent();
  expect(adminComment).toBeTruthy();
  expect(playerComment).toBe(adminComment);

  // 10. mismo estado: quien tiene el turno tira dados y AMBOS ven el resultado
  const adminHasTurn = (await admin.getByTestId('turn-panel').textContent())?.includes('sos vos');
  const roller = adminHasTurn ? admin : player;
  await roller.getByTestId('roll-dice').click();
  await expect(admin.getByTestId('dice-result')).toBeVisible({ timeout: 10_000 });
  await expect(player.getByTestId('dice-result')).toBeVisible();
  const adminDice = await admin.getByTestId('dice-result').textContent();
  const playerDice = await player.getByTestId('dice-result').textContent();
  expect(adminDice).toBe(playerDice);

  await admin.screenshot({ path: 'test-results/slice-admin-board.png', fullPage: true });
  await player.screenshot({ path: 'test-results/slice-player-board.png', fullPage: true });

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
