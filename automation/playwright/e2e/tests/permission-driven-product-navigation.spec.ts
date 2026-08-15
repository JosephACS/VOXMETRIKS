import { test, expect, type Page, type Locator } from '@playwright/test';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

/**
 * Spec 054 — permission-driven navigation on isolated DuckDB + API.
 * Normal pointer/keyboard only — no force, evaluate(click), skips or fallback goto.
 */

const API = process.env.E2E_API_URL || 'http://127.0.0.1:8013/api/v1';
const API_ORIGIN = API.replace(/\/api\/v1\/?$/, '');
const PERSONAS_PATH =
  process.env.E2E_054_PERSONAS ||
  path.join(process.env.TEMP || os.tmpdir(), 'voxmetrik-054-e2e', 'personas.json');

interface Persona {
  email: string;
  username: string;
  password: string;
  token: string;
  userId?: number;
  orgId?: number;
  claimed?: boolean;
}

interface PersonasFile {
  apiBase: string;
  orgId: number;
  owner: Persona;
  analyst: Persona;
  billing: Persona;
  viewer: Persona;
  engineer: Persona;
  platformAdmin: Persona;
  artist: Persona;
}

function loadPersonas(): PersonasFile {
  if (!fs.existsSync(PERSONAS_PATH)) {
    throw new Error(
      `FAIL-CLOSED: personas file missing at ${PERSONAS_PATH}. Run npm run e2e:054`,
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
  if (!String(process.env.DB_PATH).includes('voxmetrik-054-e2e')) {
    throw new Error(`FAIL-CLOSED: DB_PATH must be under voxmetrik-054-e2e: ${process.env.DB_PATH}`);
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
  const sidebarOpen = await shell.evaluate((el) => el.classList.contains('sidebar-open'));
  if (sidebarOpen) {
    await expect(page.getByTestId('app-sidebar-nav')).toBeVisible({ timeout: 5_000 });
    return;
  }
  const toggle = page.locator('button.menu-btn').first();
  // Desktop hides the menu button — sidebar is always docked.
  if (!(await toggle.isVisible().catch(() => false))) {
    await expect(page.getByTestId('app-sidebar-nav')).toBeVisible({ timeout: 5_000 });
    return;
  }
  await toggle.click();
  await expect(shell).toHaveClass(/sidebar-open/, { timeout: 15_000 });
  await expect(page.getByTestId('app-sidebar-nav')).toBeVisible({ timeout: 15_000 });
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
    /\/(discover|workpanel|welcome|spaces|artist-space|first-access|account|platform-ops|catalog|organizations|elt-pipeline|reports)/,
    { timeout: 60_000 },
  );
  await expect(page.getByTestId('app-shell')).toBeVisible({ timeout: 30_000 });
}

/**
 * Enter a space via chooser testid or header space-selector (kind-scoped).
 * Does not match ambiguous labels like bare "admin".
 */
async function enterSpaceByKind(
  page: Page,
  kind: 'organization' | 'data_ops' | 'platform_admin' | 'personal' | 'artist',
  options?: { orgLabelHint?: string; orgId?: number },
): Promise<void> {
  const chooser = page.getByTestId(`space-choice-${kind}`);
  let enteredViaChooser = false;

  if (kind === 'organization' && options?.orgLabelHint) {
    const named = page
      .getByTestId('space-chooser-page')
      .getByRole('button', { name: new RegExp(options.orgLabelHint, 'i') });
    if (await named.isVisible().catch(() => false)) {
      await named.click();
      enteredViaChooser = true;
    } else {
      const labeled = page
        .getByRole('main')
        .getByRole('button', { name: new RegExp(options.orgLabelHint, 'i') });
      if (await labeled.isVisible().catch(() => false)) {
        await labeled.click();
        enteredViaChooser = true;
      }
    }
  } else if (await chooser.first().isVisible().catch(() => false)) {
    await chooser.first().click();
    enteredViaChooser = true;
  }

  const selector = page.getByTestId('space-selector');
  const selectorVisible = await selector.isVisible().catch(() => false);

  if (!enteredViaChooser && selectorVisible) {
    await selector.getByRole('button').first().click();
    let item = page.getByTestId(`space-selector-item-${kind}`);
    if (kind === 'organization' && options?.orgLabelHint) {
      item = page
        .locator('.space-selector-item')
        .filter({ hasText: new RegExp(options.orgLabelHint, 'i') })
        .first();
    }
    await expect(item.first()).toBeVisible({ timeout: 10_000 });
    await item.first().click();
  } else if (!enteredViaChooser && !selectorVisible) {
    // Space selector is hidden when only one space exists (typical personal-only).
    if (kind !== 'personal') {
      await expect(selector).toBeVisible({ timeout: 20_000 });
    }
  }

  if (await selector.isVisible().catch(() => false)) {
    if (kind === 'organization' && options?.orgLabelHint) {
      await expect(selector).toContainText(new RegExp(options.orgLabelHint, 'i'), {
        timeout: 20_000,
      });
    } else if (kind === 'platform_admin') {
      await expect(selector).toContainText(
        /platform administration|administraci[oó]n de plataforma/i,
        { timeout: 20_000 },
      );
    } else if (kind === 'data_ops') {
      await expect(selector).toContainText(/data ops|datos/i, { timeout: 20_000 });
    }
  }

  await openMobileNavIfNeeded(page);
  await expandAllNavGroups(page);

  if (kind === 'organization' && options?.orgId != null) {
    const orgHref = `/organizations/${options.orgId}`;
    await expect(
      page.getByTestId('app-sidebar-nav').locator(`a[href="${orgHref}"], a[href^="${orgHref}/"]`).first(),
    ).toBeVisible({ timeout: 25_000 });
  }
}

async function selectOrganizationSpace(page: Page, orgLabelHint: string, orgId: number): Promise<void> {
  await enterSpaceByKind(page, 'organization', { orgLabelHint, orgId });
}

function sidebarLinks(page: Page): Locator {
  return page.getByTestId('app-sidebar-nav').locator('a[href]');
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

async function assertNoAccessDenied(page: Page): Promise<void> {
  const url = page.url();
  expect(url).not.toMatch(/\/error\/403/);
  expect(url).not.toMatch(/\/organizations\/access-denied/);
  const denied = page.getByText(/acceso denegado|access denied/i).first();
  await expect(denied).toHaveCount(0);
}

function isSoftApiDenial(url: string): boolean {
  // Known soft probes that pages tolerate without hard-blocking the surface
  // (catchError → empty); must not fail the org-scoped link walk.
  return (
    url.includes('/reports/simple/catalog') ||
    url.includes('/reports/complex/catalog') ||
    (url.includes('/api/v1/tracks/') && url.includes('/cover')) ||
    // Business Analytics dashboard enriches with CRM board data when present.
    url.includes('/api/v1/crm/opportunities')
  );
}

async function walkOrganizationScopedLinks(page: Page, hrefs: string[]): Promise<void> {
  const orgScoped = hrefs.filter((h) => {
    if (h.startsWith('/account') || h === '/settings' || h === '/discover') return false;
    return (
      h.startsWith('/organizations') ||
      h.startsWith('/catalog') ||
      h.startsWith('/reports') ||
      h.startsWith('/subscriptions') ||
      h.startsWith('/billing') ||
      h.startsWith('/campaigns') ||
      h.startsWith('/business-analytics') ||
      h.startsWith('/royalties') ||
      h.startsWith('/payouts') ||
      h.startsWith('/crm') ||
      h.startsWith('/customer-success') ||
      h.startsWith('/support') ||
      h.startsWith('/compliance') ||
      h.startsWith('/artist')
    );
  });

  const unexpected: string[] = [];
  const onResponse = (res: { status: () => number; url: () => string }) => {
    const status = res.status();
    if (status !== 401 && status !== 403) return;
    const url = res.url();
    if (!url.includes('/api/v1/')) return;
    if (status === 403 && isSoftApiDenial(url)) return;
    unexpected.push(`${status} ${url}`);
  };
  page.on('response', onResponse);
  try {
    for (const href of orgScoped) {
      await clickSidebarHref(page, href);
    }
  } finally {
    page.off('response', onResponse);
  }
  expect(unexpected, unexpected.slice(0, 8).join('\n')).toEqual([]);
}

async function clickSidebarHref(page: Page, href: string): Promise<void> {
  const currentPath = new URL(page.url()).pathname;
  if (currentPath === href) {
    await assertNoAccessDenied(page);
    return;
  }

  await openMobileNavIfNeeded(page);
  await expandAllNavGroups(page);
  const nav = page.getByTestId('app-sidebar-nav');
  const link = nav.locator(`a[href="${href}"], a[href^="${href}?"]`).first();
  await expect(link).toBeVisible({ timeout: 15_000 });
  // Scroll the sidebar scroller (not the page) so mobile drawer links stay actionable.
  await nav.evaluate((el, targetHref) => {
    const anchor = Array.from(el.querySelectorAll('a')).find((a) => {
      const h = a.getAttribute('href') || '';
      return h === targetHref || h.startsWith(`${targetHref}?`);
    });
    if (!anchor) return;
    const scroller = el as HTMLElement;
    const top = (anchor as HTMLElement).offsetTop - 80;
    scroller.scrollTop = Math.max(0, top);
  }, href);
  await expect(link).toBeEnabled({ timeout: 5_000 });
  const viewport = page.viewportSize();
  const useTouch = !!viewport && viewport.width < 1024;
  if (useTouch) {
    await link.tap({ timeout: 20_000 });
  } else {
    await link.click({ timeout: 20_000 });
  }
  await page.waitForLoadState('domcontentloaded');
  await expect(page).not.toHaveURL(/\/error\/403/, { timeout: 8_000 });
  await assertNoAccessDenied(page);
}

test.describe.configure({ mode: 'serial' });

test.describe('054 permission-driven product navigation', () => {
  const personas = loadPersonas();

  test.beforeEach(async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.addInitScript(() => {
      const style = document.createElement('style');
      style.setAttribute('data-e2e-054', 'reduce-motion');
      style.textContent =
        '*,*::before,*::after{transition:none!important;animation:none!important;scroll-behavior:auto!important;}';
      const mount = () => {
        if (document.head && !document.head.querySelector('style[data-e2e-054]')) {
          document.head.appendChild(style);
        }
      };
      mount();
      document.addEventListener('DOMContentLoaded', mount);
    });
  });

  test('owner sees org edit + reports and every visible link stays authorized', async ({
    page,
  }) => {
    await login(page, personas.owner);
    await selectOrganizationSpace(page, 'Nav Matrix', personas.orgId);
    const hrefs = await collectSidebarHrefs(page);
    expect(hrefs.some((h) => h.includes(`/organizations/${personas.orgId}`))).toBe(true);
    expect(hrefs).toContain('/reports');
    expect(hrefs).toContain('/subscriptions/overview');
    expect(hrefs).not.toContain('/workpanel');

    await walkOrganizationScopedLinks(page, hrefs);

    await clickSidebarHref(page, `/organizations/${personas.orgId}`);
    const settingsTab = page.locator('.mod-chrome a.mod-chrome__tab', { hasText: /^Perfil$/ });
    if (await settingsTab.isVisible().catch(() => false)) {
      await settingsTab.click();
      await assertNoAccessDenied(page);
      await expect(page).toHaveURL(new RegExp(`/organizations/${personas.orgId}/settings`));
    }
  });

  test('analyst with report.view sees Reports and not Workpanel', async ({ page }) => {
    await login(page, personas.analyst);
    await selectOrganizationSpace(page, 'Nav Matrix', personas.orgId);
    const hrefs = await collectSidebarHrefs(page);
    expect(hrefs).toContain('/reports');
    expect(hrefs).not.toContain('/workpanel');
    expect(hrefs).not.toContain('/crm/dashboard');
    await walkOrganizationScopedLinks(page, hrefs);
  });

  test('billing manager sees billing surfaces without Reports', async ({ page }) => {
    await login(page, personas.billing);
    await selectOrganizationSpace(page, 'Nav Matrix', personas.orgId);
    const hrefs = await collectSidebarHrefs(page);
    expect(hrefs).toContain('/billing/invoices');
    expect(hrefs).toContain('/subscriptions/overview');
    expect(hrefs).not.toContain('/reports');
    await walkOrganizationScopedLinks(page, hrefs);
  });

  test('viewer surfaces stay distinct and authorized', async ({ page }) => {
    await login(page, personas.viewer);
    await selectOrganizationSpace(page, 'Nav Matrix', personas.orgId);
    const hrefs = await collectSidebarHrefs(page);
    expect(hrefs.some((h) => h.includes(`/organizations/${personas.orgId}`))).toBe(true);
    expect(hrefs).toContain('/reports');
    expect(hrefs).not.toContain('/workpanel');
    expect(hrefs).not.toContain('/royalties');
    expect(hrefs).not.toContain('/billing/invoices');
    expect(hrefs).not.toContain('/subscriptions/overview');
    await walkOrganizationScopedLinks(page, hrefs);
  });

  test('engineer data ops nav has no org commercial flash destinations', async ({ page }) => {
    await login(page, {
      ...personas.engineer,
      email: personas.engineer.username || 'engineer',
    });
    await enterSpaceByKind(page, 'data_ops');
    await expect(
      page.getByTestId('app-sidebar-nav').locator('a[href="/elt-pipeline"], a[href="/workpanel"]').first(),
    ).toBeVisible({ timeout: 20_000 });
    const hrefs = await collectSidebarHrefs(page);
    expect(hrefs).toContain('/workpanel');
    expect(hrefs).toContain('/elt-pipeline');
    expect(hrefs).toContain('/explorer');
    expect(hrefs).not.toContain('/crm/dashboard');
    expect(hrefs).not.toContain('/subscriptions/plans');
    await clickSidebarHref(page, '/elt-pipeline');
    await assertNoAccessDenied(page);
  });

  test('platform admin sees platform ops without contextless org modules', async ({ page }) => {
    await login(page, {
      ...personas.platformAdmin,
      email: personas.platformAdmin.username || 'admin',
    });
    await enterSpaceByKind(page, 'platform_admin');
    await expect(
      page.getByTestId('app-sidebar-nav').locator('a[href*="/platform-ops"]').first(),
    ).toBeVisible({ timeout: 20_000 });
    const hrefs = await collectSidebarHrefs(page);
    expect(hrefs.some((h) => h.startsWith('/platform-ops'))).toBe(true);
    expect(hrefs).not.toContain('/subscriptions/plans');
    expect(hrefs).not.toContain('/crm/dashboard');
    expect(hrefs).not.toContain('/campaigns');
    const ops = hrefs.find((h) => h.startsWith('/platform-ops'));
    if (ops) {
      await clickSidebarHref(page, ops);
      await assertNoAccessDenied(page);
    }
  });

  test('personal entry keeps artist and organization journeys discoverable', async ({ page }) => {
    await login(page, personas.artist);
    await enterSpaceByKind(page, 'personal');
    const hrefs = await collectSidebarHrefs(page);
    expect(hrefs).toContain('/artist-space/claim');
    expect(hrefs).toContain('/organizations/new');
    await clickSidebarHref(page, '/artist-space/claim');
    await assertNoAccessDenied(page);
  });
});
