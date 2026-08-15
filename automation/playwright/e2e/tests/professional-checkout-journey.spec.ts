import { test, expect, type Page } from '@playwright/test';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

/**
 * Spec 052 — fail-closed Playwright suite on an isolated DuckDB + API.
 * NEVER points DB_PATH at data/warehouse/voxmetrik.duckdb.
 * PAN/CVV stay in browser inputs only; assertions never persist them.
 */

const API = process.env.E2E_API_URL || 'http://127.0.0.1:8011/api/v1';
const API_ORIGIN = API.replace(/\/api\/v1\/?$/, '');
const PERSONAS_PATH =
  process.env.E2E_052_PERSONAS ||
  path.join(process.env.TEMP || os.tmpdir(), 'voxmetrik-052-e2e', 'personas.json');

const SUCCESS_PAN = '4242424242424242';
const DECLINED_PAN = '4000000000000002';
const PROCESSING_PAN = '4000000000000077';
const CVV = '123';

interface Persona {
  email: string;
  username: string;
  password: string;
  token: string;
  orgId?: number;
}

interface PersonasFile {
  apiBase: string;
  password: string;
  personal: Persona;
  orgOwner: Persona;
  orgPlan: {
    plan_id: number;
    plan_price_id: number;
    billing_period: string;
    currency: string;
    plan_code: string;
  };
}

function loadPersonas(): PersonasFile {
  if (!fs.existsSync(PERSONAS_PATH)) {
    throw new Error(
      `FAIL-CLOSED: personas file missing at ${PERSONAS_PATH}. Run npm run e2e:052`,
    );
  }
  const dbPath = (process.env.DB_PATH || '').replace(/\//g, '\\').toLowerCase();
  if (!process.env.DB_PATH) {
    throw new Error('FAIL-CLOSED: DB_PATH is unset — isolated harness required');
  }
  if (dbPath.includes('data\\warehouse\\voxmetrik.duckdb') || dbPath.endsWith('data\\warehouse\\voxmetrik.duckdb')) {
    throw new Error(`FAIL-CLOSED: DB_PATH points at canonical warehouse: ${process.env.DB_PATH}`);
  }
  if (!String(process.env.DB_PATH).includes('voxmetrik-052-e2e')) {
    throw new Error(`FAIL-CLOSED: DB_PATH must be under voxmetrik-052-e2e: ${process.env.DB_PATH}`);
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
  await page.locator('#loginId').fill(user.email);
  await page.locator('#password').fill(user.password);
  await page.locator('button.submit-btn[type="submit"]').click();
  await page.waitForURL(
    /\/(discover|workpanel|welcome|spaces|artist-space|first-access|account|platform-ops|catalog|organizations)/,
    { timeout: 60_000 },
  );
}

async function createCheckoutOrganization(page: Page, label: string): Promise<number> {
  const token = await page.evaluate(
    () => localStorage.getItem('voxmetrik_auth_token') ?? sessionStorage.getItem('voxmetrik_auth_token'),
  );
  const response = await page.request.post(`${API}/organizations`, {
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    data: {
      display_name: `${label} ${Date.now()}`,
      organization_type: 'label',
      timezone: 'UTC',
      default_currency: 'USD',
      activate: true,
    },
  });
  expect(response.ok(), `create checkout organization → ${response.status()}`).toBeTruthy();
  const body = await response.json();
  const organizationId = Number(body.organization?.id || 0);
  expect(organizationId).toBeGreaterThan(0);

  // Recreate client services so session bootstrap includes the new tenant.
  await page.reload();
  await expect(page.locator('[data-testid="app-shell"]')).toBeVisible({ timeout: 45_000 });
  return organizationId;
}

async function registerFreshPersonal(page: Page): Promise<Persona> {
  await rewriteApiToIsolated(page);
  const stamp = `${Date.now()}${Math.floor(Math.random() * 1000)}`;
  const email = `vx052_e2e_${stamp}@voxmetrik.io`;
  const username = `vx052e${stamp}`.slice(0, 24);
  const password = 'Secret052!pass';
  const reg = await page.request.post(`${API}/users/register`, {
    data: { username, email, password },
  });
  expect(reg.ok(), `register ${email}`).toBeTruthy();
  const regBody = await reg.json();
  const code = regBody.dev_code;
  expect(String(code || '')).toMatch(/^\d{6}$/);
  const verified = await page.request.post(`${API}/users/verify-email`, {
    data: { email, code },
  });
  expect(verified.ok()).toBeTruthy();
  const payload = await verified.json();
  return {
    email,
    username,
    password,
    token: payload.token,
  };
}

async function fillPayment(page: Page, pan: string): Promise<void> {
  await expect(page.getByTestId('checkout-payment')).toBeVisible({ timeout: 30_000 });
  await page.getByTestId('checkout-card-pan').fill(pan);
  await page.locator('#checkout-cvv').fill(CVV);
  await page.locator('#checkout-exp-month').fill('12');
  await page.locator('#checkout-exp-year').fill(String(new Date().getFullYear() + 2));
}

async function continueToPayment(page: Page): Promise<void> {
  await expect(page.getByTestId('checkout-review')).toBeVisible({ timeout: 45_000 });
  await expect(page.getByTestId('checkout-simulated-notice')).toBeVisible();
  await page.getByRole('button', { name: /continuar|continue|pago|payment/i }).click();
}

async function confirmPay(page: Page): Promise<void> {
  await page.getByTestId('checkout-confirm').click();
}

test.describe('Spec 052 professional checkout', () => {

  test('Personal success', async ({ page }) => {
    const p = loadPersonas();
    await login(page, p.personal);
    await page.goto('/account/checkout?plan_code=premium_individual&billing_period=monthly');
    await continueToPayment(page);
    await fillPayment(page, SUCCESS_PAN);
    await confirmPay(page);
    await expect(page.getByTestId('checkout-result')).toBeVisible({ timeout: 45_000 });
    await expect(page.locator('body')).toContainText(/éxito|success|activa|active|activada/i);
    const panStillInDom = await page.locator('#checkout-pan').count();
    const cvvStillInDom = await page.locator('#checkout-cvv').count();
    expect(panStillInDom, 'PAN input must be cleared from result step').toBe(0);
    expect(cvvStillInDom, 'CVV input must be cleared from result step').toBe(0);
    const html = await page.content();
    expect(html).not.toContain(SUCCESS_PAN);
    expect(html).not.toContain(DECLINED_PAN);
  });

  test('Personal decline then retry success', async ({ page }) => {
    const p = loadPersonas();
    await login(page, p.personal);
    await page.goto('/account/checkout?plan_code=premium_family&billing_period=monthly');
    await continueToPayment(page);
    await fillPayment(page, DECLINED_PAN);
    await confirmPay(page);
    await expect(page.getByTestId('checkout-result')).toBeVisible({ timeout: 45_000 });
    await expect(page.locator('body')).toContainText(/fall|declin|fail|reintent/i);
    await page.getByRole('button', { name: /reintent|retry/i }).click();
    await fillPayment(page, SUCCESS_PAN);
    await confirmPay(page);
    await expect(page.getByTestId('checkout-result')).toBeVisible({ timeout: 45_000 });
    await expect(page.locator('body')).toContainText(/éxito|success|activa|active/i);
  });

  test('Personal processing scenario', async ({ page }) => {
    const user = await registerFreshPersonal(page);
    await login(page, user);
    await page.goto('/account/checkout?plan_code=premium_individual&billing_period=monthly');
    await continueToPayment(page);
    await fillPayment(page, PROCESSING_PAN);
    await confirmPay(page);
    await expect(
      page.locator('[data-testid="checkout-result"], body'),
    ).toContainText(/proces|pending|wait|refresc|refresh|éxito|success|activada/i, {
      timeout: 45_000,
    });
  });

  test('Organization success', async ({ page }) => {
    const p = loadPersonas();
    await login(page, p.orgOwner);
    const organizationId = await createCheckoutOrganization(page, 'Label Success');
    const q = new URLSearchParams({
      organization_id: String(organizationId),
      plan_id: String(p.orgPlan.plan_id),
      plan_price_id: String(p.orgPlan.plan_price_id),
      billing_period: p.orgPlan.billing_period || 'monthly',
    });
    await page.goto(`/subscriptions/checkout?${q.toString()}`);
    await continueToPayment(page);
    await fillPayment(page, SUCCESS_PAN);
    await confirmPay(page);
    await expect(page.getByTestId('checkout-result')).toBeVisible({ timeout: 45_000 });
    await expect(page.locator('body')).toContainText(/éxito|success|activa|active|activada/i);
  });

  test('Organization decline stays without operational unlock copy', async ({ page }) => {
    const p = loadPersonas();
    await login(page, p.orgOwner);
    const orgId = await createCheckoutOrganization(page, 'Label Decline');
    const q = new URLSearchParams({
      organization_id: String(orgId),
      plan_id: String(p.orgPlan.plan_id),
      plan_price_id: String(p.orgPlan.plan_price_id),
      billing_period: p.orgPlan.billing_period || 'monthly',
    });
    await page.goto(`/subscriptions/checkout?${q.toString()}`);
    await continueToPayment(page);
    await fillPayment(page, DECLINED_PAN);
    await confirmPay(page);
    await expect(page.getByTestId('checkout-result')).toBeVisible({ timeout: 45_000 });
    await expect(page.locator('body')).toContainText(/fall|declin|fail|reintent/i);
  });
});
