import fs from 'node:fs';
import path from 'node:path';
import { test, expect, type Page } from '@playwright/test';
import { ADMIN_AUTH_FILE } from '../fixtures/paths';

const EVIDENCE = path.resolve(
  'C:/Users/Admin/Documents/Tarea/Ariosto/VOXMETRIKS_Entrega/reportes-implementacion-final',
);

const COMPLEX: { id: string; testId: string }[] = [
  { id: 'streams-by-day', testId: 'visualization-temporal-line' },
  { id: 'income-by-month', testId: 'visualization-monthly-combo' },
  { id: 'top-tracks-period', testId: 'visualization-leaderboard' },
  { id: 'top-artists-period', testId: 'visualization-artist-treemap' },
  { id: 'top-genres-period', testId: 'visualization-genre-composition' },
  { id: 'opportunity-win-rate-month', testId: 'visualization-percent-trend' },
  { id: 'subscription-growth-month', testId: 'visualization-subscription-columns' },
  { id: 'releases-status-month', testId: 'visualization-stacked-status' },
  { id: 'campaign-roi', testId: 'visualization-unavailable' },
];

async function shot(page: Page, name: string): Promise<void> {
  fs.mkdirSync(EVIDENCE, { recursive: true });
  await page.screenshot({
    path: path.join(EVIDENCE, name),
    fullPage: true,
  });
}

test.use({ storageState: ADMIN_AUTH_FILE });

test.describe('Reports B-Escenario smoke', () => {
  test('hub + complex visualizations + mobile samples', async ({ page, browser }) => {
    const results: Record<string, unknown> = {
      hub: false,
      complex: {} as Record<string, string>,
      playerStaff: false,
      mobile: false,
      errors: [] as string[],
    };

    page.on('pageerror', (err) => {
      (results.errors as string[]).push(err.message);
    });

    await page.goto('/reports');
    await expect(page.locator('.reports-hub, .vx-report-page').first()).toBeVisible({ timeout: 30_000 });

    const section = page.locator('.vx-report-section__toggle, details.vx-report-section summary').first();
    if (await section.count()) {
      await section.click();
    }

    const search = page.getByTestId('reports-hub-search').or(page.locator('input[placeholder*="Buscar"]')).first();
    if (await search.count()) {
      await search.fill('streams');
      await page.waitForTimeout(300);
      await search.fill('');
    }
    await shot(page, '01-hub-desktop.png');
    results.hub = true;

    await page.goto('/simple-reports?report=business-alerts-open');
    await page.waitForTimeout(800);
    await shot(page, '02-simple-positive-zero.png');

    for (const c of COMPLEX) {
      await page.goto(`/complex-reports?report=${c.id}`);
      await page.waitForTimeout(1200);
      const viz = page.getByTestId(c.testId);
      await expect(viz).toBeVisible({ timeout: 25_000 });
      (results.complex as Record<string, string>)[c.id] = c.testId;

      const fileMap: Record<string, string> = {
        'streams-by-day': '03-streams-desktop.png',
        'income-by-month': '04-income-desktop.png',
        'top-tracks-period': '05-top-tracks-desktop.png',
        'top-artists-period': '06-top-artists-desktop.png',
        'top-genres-period': '07-genres-desktop.png',
        'opportunity-win-rate-month': '08-win-rate-desktop.png',
        'subscription-growth-month': '09-subscriptions-desktop.png',
        'releases-status-month': '10-releases-desktop.png',
        'campaign-roi': '11-campaign-roi-desktop.png',
      };
      await shot(page, fileMap[c.id]);
    }

    // Player clearance: chart useful zone (center) must sit above staff mini-player
    await page.goto('/complex-reports?report=streams-by-day');
    const chart = page.getByTestId('visualization-temporal-line');
    await chart.scrollIntoViewIfNeeded();
    await page.waitForTimeout(400);
    const chartBox = await chart.boundingBox();
    const player = page.getByTestId('player-bar');
    await expect(player).toHaveClass(/player-bar--staff/);
    const playerBox = await player.boundingBox();
    if (chartBox && playerBox) {
      const chartCenterY = chartBox.y + chartBox.height * 0.45;
      const occludesUseful = chartCenterY >= playerBox.y;
      expect(occludesUseful).toBeFalsy();
      results.playerStaff = !occludesUseful;
    } else {
      results.playerStaff = false;
    }

    const mobile = await browser.newContext({
      storageState: ADMIN_AUTH_FILE,
      viewport: { width: 390, height: 844 },
    });
    const mpage = await mobile.newPage();
    await mpage.goto('/reports');
    await mpage.waitForTimeout(600);
    await mpage.screenshot({ path: path.join(EVIDENCE, '12-hub-mobile.png'), fullPage: true });
    await mpage.goto('/complex-reports?report=streams-by-day');
    await expect(mpage.getByTestId('visualization-temporal-line')).toBeVisible({ timeout: 25_000 });
    await mpage.screenshot({ path: path.join(EVIDENCE, '13-streams-mobile.png'), fullPage: true });
    await mpage.goto('/complex-reports?report=top-tracks-period');
    await expect(mpage.getByTestId('visualization-leaderboard')).toBeVisible({ timeout: 25_000 });
    await mpage.screenshot({ path: path.join(EVIDENCE, '14-top-tracks-mobile.png'), fullPage: true });
    await mpage.goto('/complex-reports?report=top-genres-period');
    await expect(mpage.getByTestId('visualization-genre-composition')).toBeVisible({ timeout: 25_000 });
    await mpage.screenshot({ path: path.join(EVIDENCE, '15-genres-mobile.png'), fullPage: true });
    results.mobile = true;
    await mobile.close();

    fs.writeFileSync(
      path.join(EVIDENCE, 'SMOKE_RESULT.json'),
      JSON.stringify(
        {
          ...results,
          complexCount: Object.keys(results.complex as object).length,
          timestamp: new Date().toISOString(),
        },
        null,
        2,
      ),
      'utf8',
    );
  });
});
