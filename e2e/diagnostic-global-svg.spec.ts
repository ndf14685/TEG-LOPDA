import { test, expect, type APIRequestContext } from '@playwright/test';

const ADMIN = { 'X-Admin-Token': 'dev-admin' };
const API = 'http://localhost:8124';

/** DIAGNÓSTICO (no fix): ¿qué elemento recibe el click en el centro de un
 * territorio propio del SVG global en colocación? */
test('diagnóstico: interceptor de clicks en el SVG global modo 50', async ({ browser, request }) => {
  const gameRes = await (await request.post(`${API}/api/admin/games`, {
    headers: ADMIN,
    data: { name: 'diag-global', config: { game_mode: 'classic_50', commentator_enabled: false } },
  })).json();
  const gid = gameRes.game.id;
  const inv = async (n: string) => (await request.post(`${API}/api/admin/games/${gid}/players`, {
    headers: ADMIN, data: { nickname: n, color: n === 'A' ? 'red' : 'blue' },
  })).json();
  const i1 = await inv('A'); const i2 = await inv('B');
  const ctx = await browser.newContext();
  const p = await ctx.newPage();
  await p.goto(i1.join_url.replace(/^https?:\/\/[^/]+/, ''));
  await p.getByTestId('enter-lobby').click();
  await p.getByTestId('ready-button').click();
  const ctx2 = await browser.newContext();
  const p2 = await ctx2.newPage();
  await p2.goto(i2.join_url.replace(/^https?:\/\/[^/]+/, ''));
  await p2.getByTestId('enter-lobby').click();
  await p2.getByTestId('ready-button').click();
  await request.post(`${API}/api/admin/games/${gid}/start`, { headers: ADMIN });
  await expect(p.getByTestId('game-board')).toBeVisible({ timeout: 15_000 });
  await expect(p.locator('path.territory[data-mine="true"]').first()).toBeAttached({ timeout: 10_000 });

  const report = await p.evaluate(() => {
    const svg = document.querySelector('[data-testid="map-panel"] svg');
    if (!svg) return { error: 'sin svg' };
    const mine = svg.querySelector<SVGPathElement>('path.territory[data-mine="true"]');
    if (!mine) return { error: 'sin territorio propio' };
    const bb = mine.getBoundingClientRect();
    const cx = bb.x + bb.width / 2;
    const cy = bb.y + bb.height / 2;
    const atCenter = document.elementFromPoint(cx, cy);
    // punto en el borde superior del polígono (fuera del badge)
    const atEdge = document.elementFromPoint(bb.x + bb.width / 2, bb.y + 6);
    const describe = (el: Element | null) =>
      el ? `${el.tagName.toLowerCase()}.${(el.getAttribute('class') ?? '')} [${el.getAttribute('data-territory') ?? el.getAttribute('data-badge-id') ?? el.id}]` : 'null';
    const badges = svg.querySelectorAll('.badge-group').length;
    const badgePE = badges
      ? getComputedStyle(svg.querySelector('.badge-circle')!).pointerEvents
      : 'n/a';
    return {
      territorio: mine.id,
      centro_recibe: describe(atCenter),
      borde_recibe: describe(atEdge),
      badges_demo_horneados: badges,
      badge_pointer_events: badgePE,
    };
  });
  console.log('DIAGNÓSTICO:', JSON.stringify(report, null, 2));
  expect(report).toBeTruthy();

  // VERIFICACIÓN de interacción real sobre el mapa canónico (sin force):
  // los hitboxes son la única capa que recibe clicks. Se prueba en colocación.
  const isCanonical = await p.evaluate(() =>
    !!document.querySelector('[data-testid="map-panel"] svg[id*="canonical"]'),
  );
  if (isCanonical) {
    const mineId = await p.locator('path.territory.frontier[data-mine="true"]').first().getAttribute('id');
    const hb = p.locator(`path.territory-hitbox[data-territory="${mineId}"]`);
    // hover: el hitbox resalta el territorio visible
    await hb.hover();
    await expect(p.locator(`path#${mineId}.hb-hover`)).toBeAttached({ timeout: 5_000 });
    // click normal (sin force): abre el menú radial en colocación
    await hb.click();
    await expect(p.locator('.radial-menu')).toBeVisible({ timeout: 5_000 });
    // labels toggle apaga los nombres del mapa
    await p.getByTestId('map-panel').click({ position: { x: 5, y: 5 } }); // cierra radial
    await p.getByTestId('labels-toggle').click();
    await expect(p.locator('[data-testid="map-panel"] svg.hide-labels')).toBeAttached();
  }
  await ctx.close(); await ctx2.close();
});
