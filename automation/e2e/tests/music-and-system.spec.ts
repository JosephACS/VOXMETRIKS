import { test, expect } from '@playwright/test';
import { ADMIN_AUTH_FILE } from '../fixtures/paths';

test.describe('Música — catálogo', () => {
  test('artistas listado y búsqueda', async ({ page }) => {
    await page.goto('/artists');
    await expect(page.locator('h1').first()).toBeVisible({ timeout: 30_000 });
    const search = page.locator('input[type="search"], input[type="text"]').first();
    if (await search.isVisible()) {
      await search.fill('a');
    }
  });

  test('tracks catálogo carga', async ({ page }) => {
    await page.goto('/tracks');
    await expect(page.locator('h1, .page-title').first()).toBeVisible({ timeout: 30_000 });
  });

  test('búsqueda global', async ({ page }) => {
    await page.goto('/search');
    const input = page.getByTestId('search-input');
    await expect(input).toBeVisible({ timeout: 20_000 });
    await input.fill('rock');
    await expect(input).toHaveValue('rock');
  });

  test('géneros explorable', async ({ page }) => {
    await page.goto('/genres');
    await expect(page.locator('h1').first()).toBeVisible({ timeout: 30_000 });
  });

  test('playlists página carga', async ({ page }) => {
    await page.goto('/playlists');
    await expect(page.locator('h1').first()).toBeVisible({ timeout: 30_000 });
  });

  test('liked página carga', async ({ page }) => {
    await page.goto('/liked');
    await expect(page.locator('h1').first()).toBeVisible({ timeout: 30_000 });
  });

  test('historial pestañas', async ({ page }) => {
    await page.goto('/history');
    await expect(page.locator('h1, .vx-page-header h1').first()).toBeVisible({ timeout: 30_000 });
  });
});

test.describe('Inicio /discover', () => {
  test('KPIs y carriles', async ({ page }) => {
    await page.goto('/discover');
    await expect(page.locator('h1, .home-greeting').first()).toBeVisible({ timeout: 30_000 });
  });
});

test.describe('Datos ingeniero', () => {
  test.use({ storageState: ADMIN_AUTH_FILE });

  test('admin accede a ELT pipeline', async ({ page }) => {
    await page.goto('/elt-pipeline');
    await expect(page.locator('h1').first()).toBeVisible({ timeout: 30_000 });
    await expect(page).toHaveURL(/\/elt-pipeline/);
  });

  test('admin accede a explorador', async ({ page }) => {
    await page.goto('/explorer');
    await expect(page.locator('h1').first()).toBeVisible({ timeout: 30_000 });
    await expect(page).toHaveURL(/\/explorer/);
  });
});

test.describe('Configuración', () => {
  test('settings carga pestañas', async ({ page }) => {
    await page.goto('/settings');
    await expect(page.locator('h1').first()).toBeVisible({ timeout: 30_000 });
  });
});
