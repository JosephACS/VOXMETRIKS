import { Page, expect } from '@playwright/test';

export async function loginAs(
  page: Page,
  loginId: string,
  password: string,
): Promise<void> {
  await page.goto('/login');
  await page.locator('#loginId').fill(loginId);
  await page.locator('#password').fill(password);
  await page.locator('button.submit-btn[type="submit"]').click();
  await page.waitForURL(
    /\/(discover|workpanel|elt-pipeline|dashboard|reports|organizations)/,
    { timeout: 45_000 },
  );
  await expect(page.getByTestId('app-shell')).toBeVisible({ timeout: 20_000 });
}

export async function loginDemo(page: Page): Promise<void> {
  await loginAs(page, 'demo', 'demo123');
}

export async function loginAdmin(page: Page): Promise<void> {
  await loginAs(page, 'admin', 'admin123');
}

export async function expectLoggedIn(page: Page): Promise<void> {
  await expect(page.getByTestId('app-sidebar-nav')).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId('player-bar')).toBeVisible({ timeout: 20_000 });
}

export async function logout(page: Page): Promise<void> {
  await page.getByTestId('user-menu-btn').click();
  await page.getByTestId('logout-btn').click();
  await page.waitForURL(/\/login/, { timeout: 20_000 });
}
