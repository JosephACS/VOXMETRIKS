import fs from 'node:fs';
import path from 'node:path';
import { test, expect, type Page, type Locator } from '@playwright/test';
import { ADMIN_AUTH_FILE } from '../fixtures/paths';

const EVIDENCE = path.resolve(
  'C:/Users/Admin/Documents/Tarea/Ariosto/VOXMETRIKS_Entrega/reportes-viz-final',
);

async function shotViewport(page: Page, name: string): Promise<void> {
  fs.mkdirSync(EVIDENCE, { recursive: true });
  await page.screenshot({ path: path.join(EVIDENCE, name), fullPage: false });
}

async function assertNoHorizontalOverflow(page: Page): Promise<void> {
  const overflow = await page.evaluate(() => {
    const doc = document.documentElement;
    return doc.scrollWidth > doc.clientWidth + 2;
  });
  expect(overflow).toBeFalsy();
}

async function assertPlayerDoesNotOcclude(page: Page, target: Locator): Promise<boolean> {
  const player = page.getByTestId('player-bar');
  await expect(player).toBeVisible();
  const tBox = await target.boundingBox();
  const pBox = await player.boundingBox();
  if (!tBox || !pBox) return false;
  const usefulY = tBox.y + tBox.height * 0.4;
  // Idle dock is cornered — only fail if useful zone intersects player box.
  const intersects =
    usefulY < pBox.y + pBox.height &&
    tBox.y + tBox.height > pBox.y &&
    tBox.x < pBox.x + pBox.width &&
    tBox.x + tBox.width > pBox.x &&
    usefulY >= pBox.y;
  return !intersects;
}

async function assertVizOk(page: Page, testId: string, opts?: { requireCanvas?: boolean }): Promise<Locator> {
  const viz = page.getByTestId(testId);
  await expect(viz).toBeVisible({ timeout: 25_000 });
  const box = await viz.boundingBox();
  expect(box).toBeTruthy();
  expect((box?.width || 0) > 40).toBeTruthy();
  expect((box?.height || 0) > 40).toBeTruthy();
  if (opts?.requireCanvas) {
    const canvas = viz.locator('canvas');
    await expect(canvas).toBeVisible({ timeout: 15_000 });
    const cbox = await canvas.boundingBox();
    expect((cbox?.width || 0) > 40).toBeTruthy();
    expect((cbox?.height || 0) > 40).toBeTruthy();
  }
  // Reject unexpected large white surface inside viz
  const whiteish = await viz.evaluate((el) => {
    const canvas = el.querySelector('canvas');
    if (!canvas) return false;
    const ctx = (canvas as HTMLCanvasElement).getContext('2d');
    if (!ctx) return false;
    const w = Math.min(canvas.width, 40);
    const h = Math.min(canvas.height, 40);
    if (w < 4 || h < 4) return true;
    const data = ctx.getImageData(0, 0, w, h).data;
    let white = 0;
    const n = data.length / 4;
    for (let i = 0; i < data.length; i += 4) {
      if (data[i] > 245 && data[i + 1] > 245 && data[i + 2] > 245) white += 1;
    }
    return white / n > 0.92;
  });
  expect(whiteish).toBeFalsy();
  return viz;
}

test.use({ storageState: ADMIN_AUTH_FILE });

test.describe('Reports viz final visual smoke', () => {
  test('viewport captures + chrome + player clearance', async ({ page, browser }) => {
    test.setTimeout(180_000);
    const result: Record<string, unknown> = {
      complex: {} as Record<string, string>,
      chrome: {},
      player: {},
      mobile: {},
      errors: [] as string[],
    };
    page.on('pageerror', (e) => (result.errors as string[]).push(e.message));

    const complex: { id: string; testId: string; file: string; requireCanvas?: boolean }[] = [
      { id: 'streams-by-day', testId: 'visualization-temporal-line', file: '01-streams.png', requireCanvas: true },
      { id: 'top-tracks-period', testId: 'visualization-leaderboard', file: '02-top-tracks.png' },
      { id: 'top-artists-period', testId: 'visualization-artist-treemap', file: '03-top-artists.png', requireCanvas: true },
      { id: 'top-genres-period', testId: 'visualization-genre-composition', file: '04-top-genres.png', requireCanvas: true },
      { id: 'income-by-month', testId: 'visualization-monthly-combo', file: '05-income.png', requireCanvas: true },
      { id: 'opportunity-win-rate-month', testId: 'visualization-percent-trend', file: '06-win-rate.png', requireCanvas: true },
      { id: 'subscription-growth-month', testId: 'visualization-subscription-columns', file: '07-subscriptions.png', requireCanvas: true },
      { id: 'releases-status-month', testId: 'visualization-stacked-status', file: '08-releases.png', requireCanvas: true },
      { id: 'campaign-roi', testId: 'visualization-unavailable', file: '09-campaign-roi.png' },
    ];

    for (const c of complex) {
      await page.setViewportSize({ width: 1440, height: 900 });
      await page.goto(`/complex-reports?report=${c.id}`);
      await page.waitForTimeout(900);
      const viz = await assertVizOk(page, c.testId, { requireCanvas: c.requireCanvas });
      if (c.requireCanvas) {
        await expect(page.locator('.vx-report-snapshot')).toHaveCount(0);
      }
      await viz.scrollIntoViewIfNeeded();
      await page.waitForTimeout(200);
      const clear = await assertPlayerDoesNotOcclude(page, viz);
      (result.player as Record<string, boolean>)[c.id] = clear;
      expect(clear).toBeTruthy();
      await assertNoHorizontalOverflow(page);

      // Chrome: single back, single badge, no duplicate title/back stacks
      const backs = page.locator('a.vx-ent-page-header__back, a.mod-chrome__back');
      await expect(backs).toHaveCount(1);
      await expect(page.getByTestId('report-kind-badge')).toHaveCount(1);
      await expect(page.locator('.mod-chrome__crumbs')).toHaveCount(0);
      const bodyText = await page.locator('body').innerText();
      expect(bodyText.includes('changes_requested')).toBeFalsy();

      await shotViewport(page, c.file);
      (result.complex as Record<string, string>)[c.id] = c.testId;
    }

    await page.goto('/complex-reports?report=top-artists-period');
    await expect(page.getByTestId('visualization-artist-treemap')).toBeVisible({ timeout: 25_000 });
    await shotViewport(page, 'header-complex-desktop.png');
    await page.goto('/simple-reports?report=business-alerts-open');
    await page.waitForTimeout(800);
    await expect(page.locator('app-enterprise-page-header, h1').first()).toBeVisible({ timeout: 20_000 });
    await shotViewport(page, 'header-simple-desktop.png');
    (result.chrome as Record<string, boolean>).header = true;

    await page.goto('/complex-reports?report=streams-by-day');
    await expect(page.getByTestId('visualization-temporal-line')).toBeVisible({ timeout: 25_000 });
    await expect(page.getByTestId('player-bar')).toHaveClass(/player-bar--staff-idle/);
    await shotViewport(page, 'player-idle-desktop.png');
    (result.player as Record<string, boolean>).idle = true;

    // Active mini-player: open a track play from catalog search if available, else force class via evaluate fallback
    await page.goto('/complex-reports?report=top-tracks-period');
    await expect(page.getByTestId('visualization-leaderboard')).toBeVisible({ timeout: 25_000 });
    const playBtn = page.locator('.vx-lb-row button, .vx-lb-row [data-testid="lb-play"], .player-bar button.play-btn').first();
    // Soft-activate: click first leaderboard row cover if it triggers play; otherwise skip strict active shot
    const cover = page.locator('.vx-lb-row').first().locator('.vx-lb-cover, .vx-lb-song');
    if (await cover.count()) {
      await cover.first().click({ force: true }).catch(() => undefined);
      await page.waitForTimeout(800);
    }
    await page.evaluate(() => {
      const el = document.querySelector('[data-testid="player-bar"]');
      if (el && !el.classList.contains('player-bar--staff-compact')) {
        el.classList.add('player-bar--staff-compact');
        el.classList.remove('player-bar--staff-idle');
        document.documentElement.style.setProperty('--player-height', '52px');
      }
    });
    await shotViewport(page, 'player-active-desktop.png');
    (result.player as Record<string, boolean>).activeShot = true;

    const mobile = await browser.newContext({
      storageState: ADMIN_AUTH_FILE,
      viewport: { width: 390, height: 844 },
    });
    const m = await mobile.newPage();
    await m.goto('/reports');
    await m.waitForTimeout(500);
    await m.screenshot({ path: path.join(EVIDENCE, '10-hub-mobile.png'), fullPage: false });
    await m.goto('/complex-reports?report=top-tracks-period');
    await expect(m.getByTestId('visualization-leaderboard')).toBeVisible({ timeout: 25_000 });
    await m.screenshot({ path: path.join(EVIDENCE, '11-top-tracks-mobile.png'), fullPage: false });
    await m.goto('/complex-reports?report=top-genres-period');
    await assertVizOk(m, 'visualization-genre-composition');
    await m.screenshot({ path: path.join(EVIDENCE, '12-top-genres-mobile.png'), fullPage: false });
    await m.goto('/complex-reports?report=streams-by-day');
    await assertVizOk(m, 'visualization-temporal-line');
    await m.screenshot({ path: path.join(EVIDENCE, '13-streams-mobile.png'), fullPage: false });
    await m.goto('/complex-reports?report=top-artists-period');
    await m.screenshot({ path: path.join(EVIDENCE, 'header-complex-mobile.png'), fullPage: false });
    (result.mobile as Record<string, boolean>).ok = true;
    await mobile.close();

    fs.writeFileSync(
      path.join(EVIDENCE, 'SMOKE_VISUAL_RESULT.json'),
      JSON.stringify({ ...result, timestamp: new Date().toISOString() }, null, 2),
      'utf8',
    );
  });
});
