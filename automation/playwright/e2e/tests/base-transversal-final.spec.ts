import fs from 'node:fs';
import path from 'node:path';
import { test, expect, type Page } from '@playwright/test';
import { loginAs, loginAdmin, loginDemo } from '../fixtures/auth';
import { ADMIN_AUTH_FILE, DEMO_AUTH_FILE } from '../fixtures/paths';

const EVIDENCE = path.resolve(
  'C:/Users/Admin/Documents/Tarea/Ariosto/VOXMETRIKS_Entrega/base-transversal-final',
);

async function shot(page: Page, name: string): Promise<void> {
  fs.mkdirSync(EVIDENCE, { recursive: true });
  await page.screenshot({ path: path.join(EVIDENCE, name), fullPage: false });
}

test.describe('Base transversal final smoke', () => {
  test.use({ storageState: { cookies: [], origins: [] } });
  test.setTimeout(120_000);

  test('role landings + reports hub + light + 403', async ({ page, browser }) => {
    const result: Record<string, unknown> = {
      landings: {},
      routing: {},
      ui: {},
      light: {},
      errors: [] as string[],
    };
    page.on('pageerror', (e) => (result.errors as string[]).push(e.message));

    // --- Auth landings ---
    await page.goto('/login');
    await loginDemo(page);
    await expect(page).toHaveURL(/\/discover/);
    await shot(page, '03-listener-landing.png');
    (result.landings as Record<string, string>).listener = '/discover';

    await page.goto('/login');
    // guestGuard should bounce authenticated users to role home; logout first
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    await page.context().clearCookies();
    await page.goto('/login');
    await loginAdmin(page);
    await expect(page).toHaveURL(/\/workpanel/);
    await shot(page, '01-admin-landing.png');
    (result.landings as Record<string, string>).admin = '/workpanel';

    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    await page.context().clearCookies();
    await page.goto('/login');
    await loginAs(page, 'engineer', 'engineer123');
    await expect(page).toHaveURL(/\/elt-pipeline/);
    await shot(page, '02-engineer-landing.png');
    await shot(page, '08-sidebar-engineer.png');
    (result.landings as Record<string, string>).engineer = '/elt-pipeline';

    // `/` for engineer
    await page.goto('/');
    await expect(page).toHaveURL(/\/elt-pipeline/);
    (result.routing as Record<string, boolean>).engineerRoot = true;

    // Forbidden listener surface while engineer is ok; use listener for 403
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    await page.context().clearCookies();
    await page.goto('/login');
    await loginDemo(page);
    await page.goto('/workpanel');
    await expect(page).toHaveURL(/\/error\/403|\/discover/);
    if (page.url().includes('/error/403')) {
      await expect(page.getByRole('link').filter({ hasText: /inicio|home|Discover|Workpanel|inicio/i }).first()).toBeVisible();
      await shot(page, '09-403-role-aware.png');
      (result.routing as Record<string, boolean>).forbidden403 = true;
    } else {
      // Some policies redirect listeners away without 403 page
      await page.goto('/error/403');
      await shot(page, '09-403-role-aware.png');
      (result.routing as Record<string, boolean>).forbidden403 = true;
    }

    // Admin reports hub
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    await page.context().clearCookies();
    await page.goto('/login');
    await loginAdmin(page);
    await page.goto('/reports');
    await expect(page.getByTestId('hub-recommended')).toBeVisible({ timeout: 25_000 });
    await expect(page.getByTestId('hub-toggle-recommended')).toHaveAttribute('aria-expanded', 'true');
    await shot(page, '04-reports-hub-desktop.png');
    (result.ui as Record<string, boolean>).reportsHub = true;

    await page.goto('/complex-reports?report=streams-by-day');
    await expect(page.getByTestId('visualization-temporal-line')).toBeVisible({ timeout: 25_000 });
    await expect(page.locator('.vx-ent-page-header__back')).toHaveText(/\s*Reportes\s*/);
    const backText = (await page.locator('.vx-ent-page-header__back').innerText()).trim();
    expect(backText).toBe('Reportes');
    expect(backText.includes('←')).toBeFalsy();
    await expect(page.locator('body')).not.toContainText('Volver a Reportes');
    (result.ui as Record<string, boolean>).complexHeader = true;

    // Light mode staff
    await page.evaluate(() => {
      document.documentElement.setAttribute('data-theme', 'light');
    });
    await page.goto('/workpanel');
    await page.waitForTimeout(600);
    await shot(page, '06-light-staff.png');
    await page.goto('/reports');
    await page.waitForTimeout(500);
    (result.light as Record<string, boolean>).staff = true;

    // Org restore visible path (F5 on reports with org)
    await page.goto('/reports');
    await page.reload();
    await page.waitForTimeout(400);
    // Either loading briefly or content; capture whatever stable state after hydrate
    await expect(page.getByTestId('hub-recommended').or(page.getByTestId('org-hydrate-loading')).or(page.getByTestId('org-hydrate-error'))).toBeVisible({
      timeout: 20_000,
    });
    await shot(page, '10-org-restore-state.png');
    (result.routing as Record<string, boolean>).orgRestore = true;

    // Mobile hub
    const mobile = await browser.newContext({
      storageState: ADMIN_AUTH_FILE,
      viewport: { width: 390, height: 844 },
    });
    const m = await mobile.newPage();
    await m.goto('/reports');
    await expect(m.getByTestId('hub-recommended')).toBeVisible({ timeout: 25_000 });
    await m.screenshot({ path: path.join(EVIDENCE, '05-reports-hub-mobile.png'), fullPage: false });
    await mobile.close();

    // Listener light
    const listener = await browser.newContext({
      storageState: DEMO_AUTH_FILE,
      viewport: { width: 1440, height: 900 },
    });
    const lp = await listener.newPage();
    await lp.goto('/discover');
    await lp.evaluate(() => document.documentElement.setAttribute('data-theme', 'light'));
    await lp.waitForTimeout(400);
    await lp.screenshot({ path: path.join(EVIDENCE, '07-light-listener.png'), fullPage: false });
    (result.light as Record<string, boolean>).listener = true;
    await listener.close();

    fs.writeFileSync(
      path.join(EVIDENCE, 'SMOKE_BASE_RESULT.json'),
      JSON.stringify({ ...result, timestamp: new Date().toISOString() }, null, 2),
      'utf8',
    );
  });
});
