import { test, expect, type Page, type Locator } from '@playwright/test';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

/**
 * Spec 055 — platform admin professional journey on isolated DuckDB + API.
 * Normal pointer/keyboard only — no force, evaluate(click), skips or fallback goto.
 */

const API = process.env.E2E_API_URL || 'http://127.0.0.1:8014/api/v1';
const API_ORIGIN = API.replace(/\/api\/v1\/?$/, '');
const PERSONAS_PATH =
  process.env.E2E_055_PERSONAS ||
  path.join(process.env.TEMP || os.tmpdir(), 'voxmetrik-055-e2e', 'personas.json');

interface Persona {
  email: string;
  username: string;
  password: string;
  token: string;
  userId?: number;
}

interface PersonasFile {
  apiBase: string;
  platformAdmin: Persona;
  applicant?: Persona | null;
  pendingArtistRequest?: { id: number | null; proposed_display_name?: string } | null;
  pendingArtistRequests?: Array<{ id: number; proposed_display_name?: string }>;
}

function loadPersonas(): PersonasFile {
  if (!fs.existsSync(PERSONAS_PATH)) {
    throw new Error(
      `FAIL-CLOSED: personas file missing at ${PERSONAS_PATH}. Run npm run e2e:055`,
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
  if (!String(process.env.DB_PATH).includes('voxmetrik-055-e2e')) {
    throw new Error(`FAIL-CLOSED: DB_PATH must be under voxmetrik-055-e2e: ${process.env.DB_PATH}`);
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
    /\/(discover|workpanel|welcome|spaces|artist-space|first-access|account|platform-ops|catalog|organizations|elt-pipeline|reports|settings)/,
    { timeout: 60_000 },
  );
  await expect(page.getByTestId('app-shell')).toBeVisible({ timeout: 30_000 });
}

async function enterPlatformAdminSpace(page: Page): Promise<void> {
  const chooser = page.getByTestId('space-choice-platform_admin');
  let enteredViaChooser = false;
  if (await chooser.first().isVisible().catch(() => false)) {
    await chooser.first().click();
    enteredViaChooser = true;
  }

  const selector = page.getByTestId('space-selector');
  const selectorVisible = await selector.isVisible().catch(() => false);

  if (!enteredViaChooser && selectorVisible) {
    await selector.getByRole('button').first().click();
    const item = page.getByTestId('space-selector-item-platform_admin');
    await expect(item.first()).toBeVisible({ timeout: 10_000 });
    await item.first().click();
  } else if (!enteredViaChooser && !selectorVisible) {
    await expect(selector).toBeVisible({ timeout: 20_000 });
  }

  if (await selector.isVisible().catch(() => false)) {
    await expect(selector).toContainText(
      /platform administration|administraci[oó]n de plataforma/i,
      { timeout: 20_000 },
    );
  }

  await openMobileNavIfNeeded(page);
  await expandAllNavGroups(page);
  await expect(
    page.getByTestId('app-sidebar-nav').locator('a[href*="/platform-ops"]').first(),
  ).toBeVisible({ timeout: 20_000 });
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

async function collectPlatformAdminHrefs(page: Page): Promise<string[]> {
  await openMobileNavIfNeeded(page);
  await expandAllNavGroups(page);
  const hrefs = await sidebarLinks(page).evaluateAll((els) =>
    els
      .map((el) => (el as HTMLAnchorElement).getAttribute('href') || '')
      .filter(Boolean)
      .map((h) => h.split('?')[0]),
  );
  const unique = [...new Set(hrefs)];
  return unique.filter((h) => {
    if (h.startsWith('/platform-ops')) return true;
    // Other platform_admin registry destinations that may appear in the sidebar.
    return (
      h === '/workpanel' ||
      h === '/reports' ||
      h === '/settings' ||
      h.startsWith('/simple-reports') ||
      h.startsWith('/complex-reports') ||
      h.startsWith('/account')
    );
  });
}

async function assertNoAccessDenied(page: Page): Promise<void> {
  const url = page.url();
  expect(url).not.toMatch(/\/error\/403/);
  expect(url).not.toMatch(/\/organizations\/access-denied/);
  const denied = page.getByText(/acceso denegado|access denied/i).first();
  await expect(denied).toHaveCount(0);
}

function isSoftApiDenial(url: string): boolean {
  return (
    url.includes('/reports/simple/catalog') ||
    url.includes('/reports/complex/catalog') ||
    (url.includes('/api/v1/tracks/') && url.includes('/cover'))
  );
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
  // Scroll the sidebar scroller (not click) so mobile drawer links stay actionable.
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
  await nav.evaluate((el, targetHref) => {
    const anchor = Array.from(el.querySelectorAll('a')).find((a) => {
      const h = a.getAttribute('href') || '';
      return h === targetHref || h.startsWith(`${targetHref}?`);
    }) as HTMLElement | undefined;
    if (!anchor) return;
    let scroller: HTMLElement = el;
    let node: HTMLElement | null = el;
    while (node) {
      const style = window.getComputedStyle(node);
      if (
        /(auto|scroll)/.test(style.overflowY) &&
        node.scrollHeight > node.clientHeight + 4
      ) {
        scroller = node;
        break;
      }
      node = node.parentElement;
    }
    const top = anchor.offsetTop - 80;
    scroller.scrollTop = Math.max(0, top);
    anchor.focus();
  }, href);
  // Keyboard activation is a normal interaction and works in the mobile drawer.
  await link.focus();
  await page.keyboard.press('Enter');
  await page.waitForLoadState('domcontentloaded');
  await expect(page).not.toHaveURL(/\/error\/403/, { timeout: 8_000 });
  await assertNoAccessDenied(page);
}

async function walkPlatformAdminLinks(page: Page, hrefs: string[]): Promise<void> {
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
    for (const href of hrefs) {
      await clickSidebarHref(page, href);
    }
  } finally {
    page.off('response', onResponse);
  }
  expect(unexpected, unexpected.slice(0, 8).join('\n')).toEqual([]);
}

async function exerciseArtistRequestMutations(page: Page): Promise<void> {
  await clickSidebarHref(page, '/platform-ops/artist-requests');
  await expect(page.getByTestId('platform-artist-requests')).toBeVisible({ timeout: 30_000 });

  const rejectBtn = page.locator('[data-testid^="artist-request-reject-"]').first();
  await expect(rejectBtn).toBeVisible({ timeout: 30_000 });

  const rejectTestId = await rejectBtn.getAttribute('data-testid');
  const idMatch = rejectTestId?.match(/artist-request-reject-(\d+)/);
  const requestId = idMatch?.[1];
  expect(requestId, 'pending artist request id').toBeTruthy();

  // Invalid: reject without reason — confirmation stays + validation message.
  await rejectBtn.click();
  const reason = page.getByTestId(`artist-request-reject-reason-${requestId}`);
  const confirm = page.getByTestId(`artist-request-reject-confirm-${requestId}`);
  await expect(reason).toBeVisible({ timeout: 10_000 });
  await reason.fill('   ');
  await confirm.click();
  await expect(page.locator('.err[role="alert"]').first()).toBeVisible({ timeout: 10_000 });
  await expect(confirm).toBeVisible();

  // Successful: reject with a valid reason through the production UI.
  await reason.fill('E2E Spec 055 rejection reason — incomplete evidence');
  await confirm.click();
  await expect(page.getByTestId('platform-artist-requests')).toBeVisible({ timeout: 30_000 });
  // Request should leave the pending list (empty or without this id).
  await expect(page.getByTestId(`artist-request-reject-${requestId}`)).toHaveCount(0, {
    timeout: 30_000,
  });

}

test.describe.configure({ mode: 'serial' });

test.describe('055 platform admin professional journey', () => {
  const personas = loadPersonas();

  test.beforeEach(async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.addInitScript(() => {
      const style = document.createElement('style');
      style.setAttribute('data-e2e-055', 'reduce-motion');
      style.textContent =
        '*,*::before,*::after{transition:none!important;animation:none!important;scroll-behavior:auto!important;}';
      const mount = () => {
        if (document.head && !document.head.querySelector('style[data-e2e-055]')) {
          document.head.appendChild(style);
        }
      };
      mount();
      document.addEventListener('DOMContentLoaded', mount);
    });
  });

  test('platform admin walks every visible link and exercises mutations', async ({ page }) => {
    expect(
      personas.pendingArtistRequests?.length,
      'one required pending mutation fixture per viewport',
    ).toBeGreaterThanOrEqual(2);
    await login(page, {
      ...personas.platformAdmin,
      email: personas.platformAdmin.email || personas.platformAdmin.username || 'admin',
    });
    await enterPlatformAdminSpace(page);

    const hrefs = await collectPlatformAdminHrefs(page);
    expect(hrefs.some((h) => h.startsWith('/platform-ops'))).toBe(true);
    expect(hrefs).toContain('/platform-ops');
    expect(hrefs).toContain('/platform-ops/system');
    expect(hrefs).toContain('/platform-ops/artist-requests');

    await walkPlatformAdminLinks(page, hrefs);

    await exerciseArtistRequestMutations(page);
  });
});
