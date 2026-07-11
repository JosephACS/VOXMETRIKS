import { test, expect } from '@playwright/test';
import { loginAs, loginDemo, loginAdmin, expectLoggedIn, logout } from '../fixtures/auth';

test.describe('Acceso e identidad', () => {
  test('login demo redirige a inicio', async ({ page }) => {
    await loginDemo(page);
    await expect(page).toHaveURL(/\/discover/);
    await expectLoggedIn(page);
  });

  test('login admin funciona', async ({ page }) => {
    await loginAdmin(page);
    await expectLoggedIn(page);
  });

  test('sesión persiste tras recargar', async ({ page }) => {
    await loginDemo(page);
    await page.reload();
    await expect(page).not.toHaveURL(/\/login/);
    await expectLoggedIn(page);
  });

  test('oyente no accede a rutas de ingeniero', async ({ page }) => {
    await loginDemo(page);
    await page.goto('/elt-pipeline');
    await expect(page).toHaveURL(/\/dashboard/);
    await page.goto('/explorer');
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('registro muestra formulario', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('button', { name: /registr|sign up|crear cuenta/i }).click();
    await expect(page.locator('#username')).toBeVisible();
    await expect(page.locator('#reg-email')).toBeVisible();
  });
});

test.describe('Logout', () => {
  test('cerrar sesión vuelve a login', async ({ page }) => {
    await loginDemo(page);
    await logout(page);
  });
});
