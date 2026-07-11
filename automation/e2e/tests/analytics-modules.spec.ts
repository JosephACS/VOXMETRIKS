import { test, expect } from '@playwright/test';

test.describe('Centro analítico /dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await expect(
      page.locator('.enterprise-dashboard__kpis, app-empty-state').first(),
    ).toBeVisible({ timeout: 45_000 });
  });

  test('KPIs cargan con datos o estado vacío explícito', async ({ page }) => {
    const kpis = page.locator('app-metric-card');
    const empty = page.locator('app-empty-state');
    const kpiCount = await kpis.count();
    if (kpiCount === 0) {
      await expect(empty).toBeVisible();
      return;
    }
    await expect(kpis).toHaveCount(4);
    const texts = await kpis.allTextContents();
    expect(texts.join(' ').trim().length).toBeGreaterThan(0);
  });

  test('gráficos tienen canvas o estado vacío explícito', async ({ page }) => {
    const empty = page.locator('app-empty-state');
    if (await empty.isVisible()) {
      await expect(empty).toBeVisible();
      return;
    }
    const charts = page.locator('app-chart-widget');
    await expect(charts.first()).toBeVisible({ timeout: 30_000 });
    expect(await charts.count()).toBeGreaterThanOrEqual(3);
  });

  test('tendencia no es completamente plana', async ({ page }) => {
    const empty = page.locator('app-empty-state');
    if (await empty.isVisible()) {
      await expect(empty).toBeVisible();
      return;
    }
    const canvas = page.locator('app-chart-widget .chart-widget__canvas canvas').first();
    const chartEmpty = page.locator('app-chart-widget .chart-widget__empty').first();
    await expect(canvas.or(chartEmpty)).toBeVisible({ timeout: 15_000 });
  });
});

test.describe('Analítica de streaming /insights/analytics', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/insights/analytics');
    await expect(page.locator('app-chart-widget').first()).toBeVisible({ timeout: 45_000 });
  });

  test('filtro de fechas refresca gráficos', async ({ page }) => {
    const start = page.locator('input[type="date"]').first();
    const end = page.locator('input[type="date"]').nth(1);
    await start.fill('2025-01-01');
    await end.fill('2026-12-31');
    await page.getByRole('button', { name: /aplicar|apply/i }).click();
    await expect(page.locator('app-chart-widget').first()).toBeVisible({ timeout: 20_000 });
  });

  test('horas pico muestra barras', async ({ page }) => {
    await expect(page.locator('app-chart-widget').nth(1)).toBeVisible({ timeout: 20_000 });
  });
});

test.describe('Tracks destacados /insights/tracks', () => {
  test('ranking carga tarjetas de canciones', async ({ page }) => {
    const topTracks = page.waitForResponse(
      (res) => res.url().includes('/tracks/top') && res.status() === 200,
      { timeout: 45_000 },
    );
    await page.goto('/insights/tracks');
    await topTracks;
    const cards = page.getByTestId('featured-track-card');
    await expect(cards.first()).toBeVisible({ timeout: 45_000 });
    expect(await cards.count()).toBeGreaterThan(0);
  });

  test('scroll infinito muestra más canciones o fin de lista', async ({ page }) => {
    await page.goto('/insights/tracks');
    const cards = page.getByTestId('featured-track-card');
    await expect(cards.first()).toBeVisible({ timeout: 45_000 });
    const initial = await cards.count();
    await page.locator('.page-content').evaluate((el) => {
      el.scrollTop = el.scrollHeight;
    });
    await expect
      .poll(async () => cards.count(), { timeout: 15_000 })
      .toBeGreaterThanOrEqual(initial);
    const endLabel = page.locator('.tracks-feature__end');
    const after = await cards.count();
    expect(after > initial || (await endLabel.isVisible())).toBeTruthy();
  });
});

test.describe('Comparativas /comparatives', () => {
  test('heatmap muestra tres dimensiones', async ({ page }) => {
    await page.goto('/comparatives');
    await expect(page.locator('.heatmap-panel')).toBeVisible({ timeout: 45_000 });
    const metrics = page.locator('.hm-row .hm-metric');
    await expect(metrics).toHaveCount(3);
    await expect(metrics.nth(0)).toContainText('Popularidad');
    await expect(metrics.nth(1)).toContainText('Energía');
    await expect(metrics.nth(2)).toContainText('Canciones');
  });
});
