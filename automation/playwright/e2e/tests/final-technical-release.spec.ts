import fs from 'node:fs';
import path from 'node:path';
import { test, expect, type Page, type APIRequestContext } from '@playwright/test';
import { loginAs, loginAdmin, loginDemo } from '../fixtures/auth';

const EVIDENCE = path.resolve(
  'C:/Users/Admin/Documents/Tarea/Ariosto/VOXMETRIKS_Entrega/FINAL_RELEASE',
);
const API = 'http://127.0.0.1:8000';
const DEMO_VISIBLE = /\bDemo\b|\bDEMO\b|demostraci[oó]n|fixture|synthetic|test organization/i;

async function shot(page: Page, name: string): Promise<void> {
  fs.mkdirSync(EVIDENCE, { recursive: true });
  await page.screenshot({ path: path.join(EVIDENCE, name), fullPage: false });
}

async function resetSession(page: Page): Promise<void> {
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  await page.context().clearCookies();
}

async function waitWorkpanelReady(page: Page, title: RegExp): Promise<void> {
  await expect(page.getByText('Restaurando organización')).toHaveCount(0, { timeout: 25_000 });
  await expect(page.locator('.wp-title')).toHaveText(title, { timeout: 25_000 });
  await expect(page.locator('.wp-period')).not.toContainText(/Sin periodos disponibles/i, {
    timeout: 25_000,
  });
  await expect(page.locator('.wp-kpis, .wp-hero, .wp-kpi').first()).toBeVisible({
    timeout: 25_000,
  });
}

async function activateOrganizationSpace(page: Page): Promise<void> {
  const selector = page.getByTestId('space-selector');
  if (!(await selector.count())) return;
  const current = ((await selector.locator('.space-selector-name').textContent()) || '').trim();
  if (current && !/plataforma|platform/i.test(current)) return;
  await selector.locator('.space-selector-btn').click();
  const items = page.locator('.space-selector-item');
  const n = await items.count();
  for (let i = 0; i < n; i++) {
    const label = ((await items.nth(i).innerText()) || '').trim();
    if (label && !/plataforma|platform/i.test(label)) {
      await items.nth(i).click();
      await expect(selector.locator('.space-selector-name')).not.toHaveText(
        /plataforma|platform/i,
        { timeout: 15_000 },
      );
      return;
    }
  }
}

async function visibleDemoHits(page: Page): Promise<string[]> {
  const text = await page.locator('body').innerText();
  const hits: string[] = [];
  for (const line of text.split('\n')) {
    const trimmed = line.trim();
    if (trimmed && DEMO_VISIBLE.test(trimmed)) hits.push(trimmed.slice(0, 160));
  }
  return hits;
}

async function loginApi(
  request: APIRequestContext,
  login: string,
  password: string,
): Promise<{ token: string; role: string }> {
  const res = await request.post(`${API}/api/v1/users/login`, {
    data: { login, password, remember: true },
  });
  expect(res.status(), `login ${login}`).toBe(200);
  const body = await res.json();
  return { token: body.token, role: body.user?.role };
}

test.describe('Final technical release smoke', () => {
  test.use({ storageState: { cookies: [], origins: [] } });
  test.setTimeout(180_000);

  test('landings, listener, admin, engineer, theme, mobile, rbac', async ({
    page,
    browser,
    request,
  }) => {
    const unexpected: string[] = [];
    page.on('pageerror', (e) => unexpected.push(`pageerror: ${e.message}`));
    page.on('response', (res) => {
      if (res.status() >= 500 && res.url().includes('/api/')) {
        unexpected.push(`http ${res.status()} ${res.url()}`);
      }
    });

    fs.mkdirSync(EVIDENCE, { recursive: true });

    // --- Anonymous ---
    await page.goto('/');
    await expect(page).toHaveURL(/\/login/);
    await page.goto('/discover');
    await expect(page).toHaveURL(/\/login/);

    // --- Listener landing + `/` ---
    await loginDemo(page);
    await expect(page).toHaveURL(/\/discover/);
    await expect(page.getByTestId('app-shell')).toBeVisible();
    await expect(page.getByTestId('theme-toggle-btn')).toBeVisible();
    await page.goto('/');
    await expect(page).toHaveURL(/\/discover/);
    await shot(page, '01-listener.png');

    // Discover → Search → play → Biblioteca
    await page.goto('/search');
    const search = page.getByTestId('search-input');
    await expect(search).toBeVisible({ timeout: 20_000 });
    await search.fill('love');
    await page.getByTestId('search-submit').click();
    await expect(page.getByTestId('search-state-results')).toBeVisible({ timeout: 25_000 });
    const playBtn = page.locator('.r-play').first();
    await expect(playBtn).toBeVisible({ timeout: 15_000 });
    const firstTitle = (await page.locator('.vx-music-title').first().innerText()).trim();
    expect(firstTitle.length).toBeGreaterThan(0);
    expect(firstTitle).not.toMatch(DEMO_VISIBLE);
    await playBtn.click();
    await expect(page.locator('.player-bar.has-track .track-title').first()).toBeVisible({
      timeout: 25_000,
    });
    const playerTitle = (await page.locator('.player-bar .track-title').first().innerText()).trim();
    expect(playerTitle.length).toBeGreaterThan(0);
    expect(playerTitle).not.toMatch(DEMO_VISIBLE);
    await expect(page.getByTestId('player-play-btn')).toBeEnabled();
    await page.goto('/liked');
    await expect(page.locator('h1').first()).toBeVisible({ timeout: 20_000 });
    const listenerDemo = await visibleDemoHits(page);
    expect(listenerDemo, `listener Demo hits: ${listenerDemo.join(' | ')}`).toEqual([]);

    // --- Admin operativo / táctico / estratégico ---
    await resetSession(page);
    await page.goto('/login');
    await loginAdmin(page);
    await expect(page).toHaveURL(/\/workpanel/);
    await waitWorkpanelReady(page, /Workpanel/);
    await page.goto('/');
    await expect(page).toHaveURL(/\/workpanel/);
    await waitWorkpanelReady(page, /Workpanel/);
    await shot(page, '02-admin.png');
    await activateOrganizationSpace(page);

    await page.goto('/catalog');
    await expect(page.getByRole('tab', { name: /Artistas/i })).toBeVisible({ timeout: 25_000 });
    await page.getByRole('tab', { name: /Artistas/i }).click();
    await expect(page.locator('main')).toContainText(/artista|sin datos|sin registros|canci/i);
    await page.goto('/catalog-review');
    await expect(
      page
        .locator('h1, h2, [role="tab"][aria-selected="true"]')
        .filter({ hasText: /Revisiones|organización|Catálogo/i })
        .first(),
    ).toBeVisible({ timeout: 25_000 });

    const orgLink = page.locator('a[href*="/organizations/"]').first();
    if (await orgLink.count()) {
      await orgLink.click();
    } else {
      await page.goto('/business');
    }
    await expect(page.locator('h1, .org-title, .vx-page-header h1').first()).toBeVisible({
      timeout: 25_000,
    });

    await page.goto('/reports');
    await expect(page.getByTestId('hub-recommended')).toBeVisible({ timeout: 25_000 });
    await shot(page, '03-reports.png');

    await page.goto('/simple-reports?report=tracks-without-cover');
    await expect(page.locator('h1, .vx-report-title, .mod-chrome__title').first()).toBeVisible({
      timeout: 25_000,
    });

    await page.goto('/complex-reports?report=streams-by-day');
    await expect(page.locator('h1, .vx-report-title, .mod-chrome__title').first()).toBeVisible({
      timeout: 25_000,
    });

    await page.goto('/business-analytics');
    await expect(page).not.toHaveURL(/\/error\/403/);
    await expect(
      page.getByTestId('strategic-direction').or(page.locator('h1')).first(),
    ).toBeVisible({ timeout: 25_000 });
    await expect(page.locator('body')).toContainText(/objetivo|KPI|estratégic|Sin datos|Reportes/i);

    const adminDemo = await visibleDemoHits(page);
    expect(adminDemo, `admin Demo hits: ${adminDemo.join(' | ')}`).toEqual([]);

    // --- Engineer ---
    await resetSession(page);
    await page.goto('/login');
    await loginAs(page, 'engineer', 'engineer123');
    await expect(page).toHaveURL(/\/workpanel/);
    await waitWorkpanelReady(page, /Estado técnico/);
    await expect(page.locator('.wp-hero__label')).toContainText(/Estado general/);
    await page.goto('/');
    await expect(page).toHaveURL(/\/workpanel/);
    await waitWorkpanelReady(page, /Estado técnico/);
    await shot(page, '04-engineer.png');

    await page.goto('/elt-pipeline');
    await expect(page.locator('h1').first()).toBeVisible({ timeout: 25_000 });
    await expect(page.locator('.elt-stage')).toHaveCount(5, { timeout: 25_000 });

    await page.goto('/explorer');
    await expect(page.locator('h1').first()).toBeVisible({ timeout: 25_000 });
    const tableBtn = page.locator('.ex-table').first();
    await expect(tableBtn).toBeVisible({ timeout: 25_000 });
    await tableBtn.click();
    await expect(page.locator('.ex-detail, .ex-panel').first()).toBeVisible({ timeout: 20_000 });

    // Dark / Light representative surfaces
    await page.goto('/workpanel');
    await waitWorkpanelReady(page, /Estado técnico/);
    await expect(page.getByTestId('theme-toggle-btn')).toBeVisible();
    await page.getByTestId('theme-toggle-btn').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', /light|dark/);
    const themeAfterToggle = await page.locator('html').getAttribute('data-theme');
    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('data-theme', themeAfterToggle || '');
    if (themeAfterToggle !== 'light') {
      await page.getByTestId('theme-toggle-btn').click();
    }
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
    await waitWorkpanelReady(page, /Estado técnico/);
    await shot(page, '05-light.png');
    await page.getByTestId('theme-toggle-btn').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');

    await resetSession(page);
    await page.goto('/login');
    await loginDemo(page);
    await page.goto('/discover');
    const currentTheme = await page.locator('html').getAttribute('data-theme');
    if (currentTheme !== 'dark') {
      await page.getByTestId('theme-toggle-btn').click();
    }
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    await page.getByTestId('theme-toggle-btn').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
    await page.getByTestId('theme-toggle-btn').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');

    // Mobile 390x844 — Discover + workpanel/estado + list surface
    const mobile = await browser.newContext({
      viewport: { width: 390, height: 844 },
      storageState: { cookies: [], origins: [] },
    });
    const mpage = await mobile.newPage();
    await loginDemo(mpage);
    await mpage.goto('/discover');
    await expect(mpage.getByTestId('app-shell')).toBeVisible();
    await expect(mpage.getByTestId('theme-toggle-btn')).toBeVisible();
    await expect(mpage.getByTestId('player-bar')).toBeVisible();
    const overflow = await mpage.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThan(24);
    await shot(mpage, '06-mobile.png');
    await mpage.goto('/liked');
    await expect(mpage.locator('h1').first()).toBeVisible({ timeout: 20_000 });
    await resetSession(mpage);
    await mpage.goto('/login');
    await loginAs(mpage, 'engineer', 'engineer123');
    await expect(mpage).toHaveURL(/\/workpanel/);
    await expect(mpage.locator('.wp-title')).toHaveText(/Estado técnico/);
    await mobile.close();

    // --- RBAC / isolation API probes (403/404, never foreign data) ---
    const listener = await loginApi(request, 'demo', 'demo123');
    expect(listener.role).toBe('user');
    const staffRes = await request.get(`${API}/api/v1/analytics/explorer/tables`, {
      headers: { Authorization: `Bearer ${listener.token}` },
    });
    expect([403, 404]).toContain(staffRes.status());

    const engineer = await loginApi(request, 'engineer', 'engineer123');
    expect(engineer.role).toBe('engineer');
    const billingRes = await request.get(`${API}/api/v1/billing/invoices`, {
      headers: { Authorization: `Bearer ${engineer.token}`, 'X-Organization-Id': '1' },
    });
    expect([403, 404]).toContain(billingRes.status());

    const admin = await loginApi(request, 'admin', 'admin123');
    const orgsRes = await request.get(`${API}/api/v1/organizations`, {
      headers: { Authorization: `Bearer ${admin.token}` },
    });
    expect(orgsRes.status()).toBe(200);
    const orgs = (await orgsRes.json()) as Array<{ id: number }>;
    expect(orgs.length).toBeGreaterThan(0);
    const orgA = orgs[0].id;
    const orgB = orgA === 1 ? 2 : 1;
    const invoicesA = await request.get(`${API}/api/v1/billing/invoices`, {
      headers: {
        Authorization: `Bearer ${admin.token}`,
        'X-Organization-Id': String(orgA),
      },
    });
    expect(invoicesA.status()).toBe(200);
    const payload = await invoicesA.json();
    const items = (payload.items || []) as Array<{ id: number }>;
    const foreignList = await request.get(`${API}/api/v1/billing/invoices`, {
      headers: {
        Authorization: `Bearer ${admin.token}`,
        'X-Organization-Id': String(orgB),
      },
    });
    expect([403, 404]).toContain(foreignList.status());
    let isolationStatus = foreignList.status();
    if (items[0]?.id) {
      const cross = await request.get(`${API}/api/v1/billing/invoices/${items[0].id}`, {
        headers: {
          Authorization: `Bearer ${admin.token}`,
          'X-Organization-Id': String(orgB),
        },
      });
      isolationStatus = cross.status();
      expect([403, 404]).toContain(cross.status());
    }

    // UI RBAC: listener staff path
    await resetSession(page);
    await page.goto('/login');
    await loginDemo(page);
    await page.goto('/workpanel');
    await expect(page).toHaveURL(/\/error\/403|\/discover/);

    await resetSession(page);
    await page.goto('/login');
    await loginAs(page, 'engineer', 'engineer123');
    await page.goto('/billing/invoices');
    await expect(page).toHaveURL(/\/error\/(403|module-unavailable)|\/workpanel/);

    const realErrors = unexpected.filter(
      (e) => !/403/.test(e) && !/module-unavailable/.test(e),
    );
    expect(realErrors, realErrors.join('\n')).toEqual([]);

    fs.writeFileSync(
      path.join(EVIDENCE, '_smoke-notes.json'),
      JSON.stringify(
        {
          isolationStatus,
          unexpected: realErrors,
          orgs: [orgA, orgB],
        },
        null,
        2,
      ),
    );
  });
});
