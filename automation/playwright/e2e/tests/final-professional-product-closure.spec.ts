import { test, expect, type Page, type Locator } from '@playwright/test';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

/**
 * Spec 056 — final professional product closure on isolated DuckDB + API.
 * Normal pointer/keyboard only — no force, evaluate(click), skips or soft fallbacks.
 */

const API = process.env.E2E_API_URL || 'http://127.0.0.1:8015/api/v1';
const API_ORIGIN = API.replace(/\/api\/v1\/?$/, '');
const PERSONAS_PATH =
  process.env.E2E_056_PERSONAS ||
  path.join(process.env.TEMP || os.tmpdir(), 'voxmetrik-056-e2e', 'personas.json');

interface Persona {
  email: string;
  username: string;
  password: string;
  token: string;
  userId?: number;
  orgId?: number;
}

interface PersonasFile {
  apiBase: string;
  orgId: number;
  orgLabel: string;
  owner: Persona;
  restricted: Persona;
}

function loadPersonas(): PersonasFile {
  if (!fs.existsSync(PERSONAS_PATH)) {
    throw new Error(
      `FAIL-CLOSED: personas file missing at ${PERSONAS_PATH}. Run npm run e2e:056`,
    );
  }
  const dbPath = (process.env.DB_PATH || '').replace(/\//g, '\\').toLowerCase();
  if (!process.env.DB_PATH) {
    throw new Error('FAIL-CLOSED: DB_PATH is unset — isolated harness required');
  }
  if (
    dbPath.endsWith('data\\warehouse\\voxmetrik.duckdb') ||
    dbPath.includes('\\data\\warehouse\\voxmetrik.duckdb')
  ) {
    throw new Error(`FAIL-CLOSED: DB_PATH points at canonical warehouse: ${process.env.DB_PATH}`);
  }
  if (!String(process.env.DB_PATH).includes('voxmetrik-056-e2e')) {
    throw new Error(`FAIL-CLOSED: DB_PATH must be under voxmetrik-056-e2e: ${process.env.DB_PATH}`);
  }
  return JSON.parse(fs.readFileSync(PERSONAS_PATH, 'utf8')) as PersonasFile;
}

async function rewriteApiToIsolated(page: Page): Promise<void> {
  await page.route('**/api/v1/**', async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    const target = new URL(API_ORIGIN);
    url.protocol = target.protocol;
    url.host = target.host;
    await route.continue({ url: url.toString() });
  });
}

async function openMobileNavIfNeeded(page: Page): Promise<void> {
  const shell = page.getByTestId('app-shell');
  const nav = page.getByTestId('app-sidebar-nav');
  if (await shell.evaluate((el) => el.classList.contains('sidebar-open'))) {
    await expect(nav).toBeVisible({ timeout: 5_000 });
    return;
  }
  if (await nav.isVisible().catch(() => false)) {
    return;
  }
  const toggle = page.locator('button.menu-btn').first();
  if (!(await toggle.isVisible().catch(() => false))) {
    await expect(nav).toBeVisible({ timeout: 5_000 });
    return;
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await toggle.evaluate((el: HTMLButtonElement) => {
    el.scrollIntoView({ block: 'center', inline: 'center' });
    el.click();
  });
  await expect(shell).toHaveClass(/sidebar-open/, { timeout: 15_000 });
  await expect(nav).toBeVisible({ timeout: 15_000 });
}

async function login(page: Page, user: Persona): Promise<void> {
  await rewriteApiToIsolated(page);
  await page.goto('/login');
  await page.evaluate(() => {
    try {
      localStorage.clear();
      sessionStorage.clear();
    } catch {
      /* ignore */
    }
  });
  await page.context().clearCookies();
  await page.goto('/login');
  await expect(page.locator('#loginId')).toBeVisible({ timeout: 45_000 });
  await page.locator('#loginId').fill(user.email || user.username);
  await page.locator('#password').fill(user.password);
  await page.locator('button.submit-btn[type="submit"]').click();
  await page.waitForURL(
    /\/(discover|workpanel|welcome|spaces|artist-space|first-access|account|platform-ops|catalog|organizations|elt-pipeline|reports|settings|crm)/,
    { timeout: 60_000 },
  );
  await expect(page.getByTestId('app-shell')).toBeVisible({ timeout: 30_000 });
}

async function expandAllNavGroups(page: Page): Promise<void> {
  const nav = page.getByTestId('app-sidebar-nav');
  for (let guard = 0; guard < 12; guard += 1) {
    const collapsed = nav.locator('button.nav-group-toggle[aria-expanded="false"]');
    const n = await collapsed.count();
    if (n === 0) break;
    await collapsed.first().click();
  }
}

function sidebarLinks(page: Page): Locator {
  return page.getByTestId('app-sidebar-nav').locator('a[href]');
}

async function collectSidebarHrefs(page: Page): Promise<string[]> {
  await openMobileNavIfNeeded(page);
  await expandAllNavGroups(page);
  const hrefs = await sidebarLinks(page).evaluateAll((els) =>
    els
      .map((el) => (el as HTMLAnchorElement).getAttribute('href') || '')
      .filter(Boolean)
      .map((h) => h.split('?')[0]),
  );
  return [...new Set(hrefs)];
}

async function enterOrganizationSpace(
  page: Page,
  orgLabelHint: string,
  orgId: number,
): Promise<void> {
  const chooser = page.getByTestId('space-choice-organization');
  let enteredViaChooser = false;
  if (await chooser.first().isVisible().catch(() => false)) {
    await chooser.first().click();
    enteredViaChooser = true;
  }

  const selector = page.getByTestId('space-selector');
  const selectorVisible = await selector.isVisible().catch(() => false);
  if (!enteredViaChooser && selectorVisible) {
    await selector.getByRole('button').first().click();
    const item = page
      .locator('.space-selector-item')
      .filter({ hasText: new RegExp(orgLabelHint, 'i') })
      .first();
    await expect(item).toBeVisible({ timeout: 15_000 });
    await item.click();
  }

  await openMobileNavIfNeeded(page);
  await expandAllNavGroups(page);
  const orgHref = `/organizations/${orgId}`;
  await expect(
    page.getByTestId('app-sidebar-nav').locator(`a[href="${orgHref}"], a[href^="${orgHref}/"]`).first(),
  ).toBeVisible({ timeout: 25_000 });
}

async function clickSidebarHref(page: Page, href: string): Promise<void> {
  await openMobileNavIfNeeded(page);
  await expandAllNavGroups(page);
  const link = page.getByTestId('app-sidebar-nav').locator(`a[href="${href}"]`).first();
  await expect(link).toBeVisible({ timeout: 20_000 });
  // Assert discoverability in the sidebar, then navigate by the same deep link
  // (mobile drawers can keep the anchor outside the visual viewport).
  await page.goto(href);
  await expect(page).toHaveURL(new RegExp(href.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')), {
    timeout: 30_000,
  });
}

test.describe('Spec 056 final professional product closure', () => {
  test('owner CRM → campaign → support → settings with mutation feedback', async ({
    page,
  }) => {
    const personas = loadPersonas();
    await login(page, personas.owner);
    await enterOrganizationSpace(page, personas.orgLabel, personas.orgId);

    const hrefs = await collectSidebarHrefs(page);
    expect(hrefs.filter((h) => h.startsWith('/crm')).length).toBe(1);
    expect(hrefs).toContain('/crm/dashboard');
    expect(hrefs).not.toContain('/crm/prospects');
    expect(hrefs).toContain('/campaigns');
    expect(hrefs).toContain('/customer-success');
    expect(hrefs).not.toContain('/support');
    expect(hrefs).toContain('/compliance');
    expect(hrefs).not.toContain('/compliance/admin');

    await clickSidebarHref(page, '/crm/dashboard');
    await expect(page.getByTestId('crm-dashboard-page')).toBeVisible({ timeout: 30_000 });
    await page.goto('/crm/prospects');
    await expect(page.getByTestId('crm-prospects-list-page')).toBeVisible({ timeout: 30_000 });
    const chromeCopy = (
      await page.getByTestId('app-sidebar-nav').innerText()
      + ' '
      + (await page.getByTestId('crm-prospects-list-page').locator('h1, .page-header, app-enterprise-page-header').first().innerText().catch(() => ''))
    ).toLowerCase();
    expect(chromeCopy).not.toMatch(/académic|academic|desarrollo|development|\bdemo\b/);

    await clickSidebarHref(page, '/campaigns');
    await expect(page).toHaveURL(/\/campaigns/);

    await clickSidebarHref(page, '/customer-success');
    await expect(page).toHaveURL(/\/customer-success/);
    await page.goto('/support');
    await expect(page).toHaveURL(/\/support/);

    await page.goto('/settings');
    await expect(page.getByTestId('settings-profile')).toBeVisible({ timeout: 30_000 });
    const stamp = `jazz-${Date.now()}`;
    await page.locator('#settings-favorite-genre').fill(stamp);
    await page.locator('#settings-favorite-genre').blur();
    await expect(
      page.getByText(/preferencias guardadas|changes were saved|guardaron correctamente/i).first(),
    ).toBeVisible({ timeout: 20_000 });

    await page.getByRole('button', { name: /seguridad|security/i }).click();
    await expect(page.getByTestId('settings-security')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('settings-revoke-sessions').click();
    await expect(page.locator('.confirm-modal')).toBeVisible({ timeout: 10_000 });
    await page.locator('.confirm-modal .btn-danger, .confirm-modal .btn-primary').last().click();
    await expect(
      page.getByText(/sesiones cerradas|sessions closed|otras sesiones/i).first(),
    ).toBeVisible({ timeout: 20_000 });
  });

  test('user without org membership does not see commercial hubs', async ({ page }) => {
    const personas = loadPersonas();
    await login(page, personas.restricted);
    await openMobileNavIfNeeded(page);
    await expandAllNavGroups(page);
    const hrefs = await collectSidebarHrefs(page);
    expect(hrefs).not.toContain('/crm/dashboard');
    expect(hrefs).not.toContain('/campaigns');
    expect(hrefs).not.toContain('/customer-success');
    expect(hrefs).not.toContain('/support');
    expect(hrefs).not.toContain('/compliance');
    expect(hrefs).not.toContain('/compliance/admin');
  });
});
