import { test, expect } from '@playwright/test';

const LISTENER_ROUTES = [
  '/discover',
  '/dashboard',
  '/insights/analytics',
  '/insights/tracks',
  '/artists',
  '/tracks',
  '/genres',
  '/audio-features',
  '/search',
  '/playlists',
  '/liked',
  '/history',
  '/analytics',
  '/trending',
  '/comparatives',
  '/recommendations',
  '/settings',
  '/users',
];

test.describe('Navegación sidebar', () => {
  for (const route of LISTENER_ROUTES) {
    test(`carga ${route}`, async ({ page }) => {
      await page.goto(route);
      await expect(page.getByTestId('app-shell')).toBeVisible({ timeout: 30_000 });
      await expect(page.locator('h1, .vx-page-header h1, .enterprise-dashboard__hero h1').first()).toBeVisible({
        timeout: 30_000,
      });
      await expect(page.getByTestId('player-bar')).toBeVisible();
    });
  }
});

test.describe('PlayerBar persistente', () => {
  test('player persiste al cambiar de ruta', async ({ page }) => {
    await page.goto('/discover');
    await expect(page.getByTestId('player-bar')).toBeVisible();
    await page.goto('/artists');
    await expect(page.getByTestId('player-bar')).toBeVisible();
    await page.goto('/dashboard');
    await expect(page.getByTestId('player-bar')).toBeVisible();
  });

  test('controles de reproducción visibles', async ({ page }) => {
    await page.goto('/discover');
    await expect(page.getByTestId('player-play-btn')).toBeVisible();
  });
});
