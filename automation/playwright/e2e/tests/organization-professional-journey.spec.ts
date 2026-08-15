import { test, expect, type Page } from '@playwright/test';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

/**
 * Spec 053 — honest UI journey on isolated DuckDB + API.
 * Product mutations under test run via UI only. API is for fixtures + final asserts.
 */

const API = process.env.E2E_API_URL || 'http://127.0.0.1:8012/api/v1';
const API_ORIGIN = API.replace(/\/api\/v1\/?$/, '');
const PERSONAS_PATH =
  process.env.E2E_053_PERSONAS ||
  path.join(process.env.TEMP || os.tmpdir(), 'voxmetrik-053-e2e', 'personas.json');

const SUCCESS_PAN = '4242424242424242';
const DECLINED_PAN = '4000000000000002';
const CVV = '123';

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
  password: string;
  owner: Persona;
  invitedViewer: Persona;
  sharedOrgId: number;
  inviteToken: string;
  orgPlan: {
    plan_id: number;
    plan_price_id: number;
    billing_period: string;
    currency: string;
    plan_code: string;
    plan_display_name?: string;
  };
}

function loadPersonas(): PersonasFile {
  if (!fs.existsSync(PERSONAS_PATH)) {
    throw new Error(
      `FAIL-CLOSED: personas file missing at ${PERSONAS_PATH}. Run npm run e2e:053`,
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
  if (!String(process.env.DB_PATH).includes('voxmetrik-053-e2e')) {
    throw new Error(`FAIL-CLOSED: DB_PATH must be under voxmetrik-053-e2e: ${process.env.DB_PATH}`);
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

async function authHeaders(page: Page, orgId?: number): Promise<Record<string, string>> {
  const token = await page.evaluate(
    () => localStorage.getItem('voxmetrik_auth_token') ?? sessionStorage.getItem('voxmetrik_auth_token'),
  );
  const headers: Record<string, string> = {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
  if (orgId) headers['X-Organization-Id'] = String(orgId);
  return headers;
}

async function assertJourney(
  page: Page,
  orgId: number,
  expected: { next_action: string; access_tier: string },
): Promise<void> {
  const headers = await authHeaders(page, orgId);
  const res = await page.request.get(`${API}/organizations/${orgId}/journey`, { headers });
  expect(res.ok(), `journey GET → ${res.status()}`).toBeTruthy();
  const body = await res.json();
  expect(body.next_action).toBe(expected.next_action);
  expect(body.access_tier).toBe(expected.access_tier);
}

async function createOrganizationViaUi(page: Page, label: string): Promise<number> {
  await page.goto('/organizations/new');
  await expect(page.getByTestId('org-create-page')).toBeVisible({ timeout: 45_000 });
  await page.locator('input[formcontrolname="display_name"]').fill(`${label} ${Date.now()}`);
  await page.locator('form button[type="submit"]').click();
  await page.waitForURL(/\/organizations(\/\d+\/onboarding|\/onboarding)/, { timeout: 60_000 });
  await expect(page.getByTestId('org-onboarding-page')).toBeVisible({ timeout: 45_000 });
  await expect(page.getByTestId('journey-plan')).toBeVisible({ timeout: 45_000 });
  const match = page.url().match(/organization_id=(\d+)/);
  if (match) return Number(match[1]);
  const headers = await authHeaders(page);
  const res = await page.request.get(`${API}/organizations/current`, { headers });
  expect(res.ok()).toBeTruthy();
  const id = Number((await res.json()).organization?.id);
  expect(id).toBeGreaterThan(0);
  return id;
}

async function fillPayment(page: Page, pan: string): Promise<void> {
  await expect(page.getByTestId('checkout-payment')).toBeVisible({ timeout: 30_000 });
  await page.getByTestId('checkout-card-pan').fill(pan);
  await page.locator('#checkout-cvv').fill(CVV);
  await page.locator('#checkout-exp-month').fill('12');
  await page.locator('#checkout-exp-year').fill(String(new Date().getFullYear() + 2));
}

async function selectPaidPlanAndCheckout(page: Page, orgId: number, plan: PersonasFile['orgPlan']): Promise<void> {
  await expect(page.getByTestId('journey-choose-plan')).toBeVisible({ timeout: 45_000 });
  await page.getByTestId('journey-choose-plan').click();
  await page.waitForURL(new RegExp(`/subscriptions/select-plan\\?.*organization_id=${orgId}`), {
    timeout: 60_000,
  });
  const planSelect = page.locator('select[formcontrolname="planId"]');
  await expect(planSelect).toBeVisible({ timeout: 45_000 });
  const labelHint = (plan.plan_display_name || plan.plan_code || '').toLowerCase();
  const optionCount = await planSelect.locator('option').count();
  let selected = false;
  for (let i = 1; i < optionCount; i++) {
    const text = ((await planSelect.locator('option').nth(i).textContent()) || '').toLowerCase();
    if (!labelHint || text.includes(labelHint)) {
      await planSelect.selectOption({ index: i });
      selected = true;
      break;
    }
  }
  if (!selected && optionCount > 1) {
    await planSelect.selectOption({ index: 1 });
  }
  await expect(page.locator('select[formcontrolname="planPriceId"] option').nth(1)).toBeAttached({
    timeout: 30_000,
  });
  const priceSelect = page.locator('select[formcontrolname="planPriceId"]');
  const priceCount = await priceSelect.locator('option').count();
  if (priceCount > 1) {
    await priceSelect.selectOption({ index: 1 });
  }
  await page.locator('select[formcontrolname="mode"]').selectOption('subscribe');
  await page.locator('form.vx-form button[type="submit"]').click();
  await page.waitForURL(new RegExp(`/subscriptions/checkout\\?.*organization_id=${orgId}`), {
    timeout: 60_000,
  });
  await expect(page.getByTestId('checkout-review')).toBeVisible({ timeout: 45_000 });
  await expect(page.getByTestId('checkout-simulated-notice')).toBeVisible();
  const continueButton = page.getByRole('button', { name: /continuar|continue|pago|payment/i });
  await expect(continueButton).toBeEnabled();
  await continueButton.click();
}

async function fixtureUnpaidInvite(
  page: Page,
  owner: Persona,
  viewerEmail: string,
): Promise<{ orgId: number; inviteToken: string }> {
  const createRes = await page.request.post(`${API}/organizations`, {
    headers: {
      Authorization: `Bearer ${owner.token}`,
      'Content-Type': 'application/json',
    },
    data: {
      display_name: `Wait Owner ${Date.now()}`,
      organization_type: 'label',
      timezone: 'UTC',
      default_currency: 'USD',
      activate: true,
      client_intent_id: `e2e-wait-${Date.now()}-${Math.random()}`,
    },
  });
  expect(createRes.ok(), `fixture org → ${createRes.status()}`).toBeTruthy();
  const orgId = Number((await createRes.json()).organization?.id);
  expect(orgId).toBeGreaterThan(0);
  const inviteRes = await page.request.post(`${API}/organizations/${orgId}/invitations`, {
    headers: {
      Authorization: `Bearer ${owner.token}`,
      'Content-Type': 'application/json',
      'X-Organization-Id': String(orgId),
    },
    data: { email: viewerEmail, role_codes: ['viewer'], ttl_days: 7 },
  });
  expect(inviteRes.ok(), `fixture invite → ${inviteRes.status()}`).toBeTruthy();
  const inviteToken = (await inviteRes.json()).invite_token;
  expect(inviteToken).toBeTruthy();
  return { orgId, inviteToken };
}

async function skipTeamAndCompleteViaUi(page: Page, orgId: number): Promise<void> {
  await page.waitForURL(new RegExp(`/organizations/onboarding\\?.*organization_id=${orgId}`), {
    timeout: 90_000,
  });
  await expect(page.getByTestId('org-onboarding-page')).toBeVisible({ timeout: 45_000 });
  await expect(page.getByTestId('journey-team')).toBeVisible({ timeout: 60_000 });
  const skipTeam = page.getByTestId('journey-skip-team');
  await expect(skipTeam).toBeEnabled();
  if ((page.viewportSize()?.width ?? 0) <= 640) {
    await skipTeam.evaluate((element) =>
      element.scrollIntoView({ block: 'center', inline: 'center', behavior: 'instant' }),
    );
    const box = await skipTeam.boundingBox();
    expect(box).not.toBeNull();
    const point = { x: box!.x + box!.width / 2, y: box!.y + box!.height / 2 };
    const hitTarget = await skipTeam.evaluate((element, { x, y }) => {
      const hit = document.elementFromPoint(x, y);
      return hit === element || (!!hit && element.contains(hit));
    }, point);
    expect(hitTarget).toBeTruthy();
    await page.touchscreen.tap(point.x, point.y);
  } else {
    await skipTeam.click();
  }
  await expect(page.getByTestId('journey-complete')).toBeVisible({ timeout: 45_000 });
  const completeJourney = page.getByTestId('journey-complete-submit');
  await expect(completeJourney).toBeEnabled();
  await completeJourney.click();
  // Poll journey until complete lands as enter_workspace (UI + server).
  await expect
    .poll(
      async () => {
        const headers = await authHeaders(page, orgId);
        const res = await page.request.get(`${API}/organizations/${orgId}/journey`, { headers });
        if (!res.ok()) return `http:${res.status()}`;
        const body = await res.json();
        return `${body.next_action}|${body.access_tier}|${body.onboarding_status}`;
      },
      { timeout: 90_000 },
    )
    .toBe('enter_workspace|operational|completed');
  const hubPattern = new RegExp(`/organizations/${orgId}(/|$|\\?)`);
  if (!hubPattern.test(page.url())) {
    const enterHub = page.getByTestId('journey-enter-hub');
    await expect(enterHub).toBeVisible({ timeout: 45_000 });
    await expect(enterHub).toBeEnabled();
    await enterHub.click();
  }
  await page.waitForURL(hubPattern, { timeout: 60_000 });
}

async function acceptInviteViaUi(page: Page, token: string): Promise<number> {
  await page.goto('/invitations/accept');
  await expect(page.getByTestId('org-accept-invite-page')).toBeVisible({ timeout: 45_000 });
  await page.getByTestId('invite-token-input').fill(token);
  await page.getByTestId('invite-accept-submit').click();
  await expect(page.getByTestId('invite-activate')).toBeVisible({ timeout: 45_000 });
  await page.getByTestId('invite-activate').click();
  await page.waitForURL(/\/organizations\/onboarding\?organization_id=\d+/, { timeout: 60_000 });
  const match = page.url().match(/organization_id=(\d+)/);
  expect(match).toBeTruthy();
  return Number(match![1]);
}

test.describe('Spec 053 organization professional journey', () => {
  test('Owner paid success path (create → plan → checkout → team skip → complete → hub)', async ({
    page,
  }) => {
    const p = loadPersonas();
    await login(page, p.owner);
    const orgId = await createOrganizationViaUi(page, 'Label Success 053');
    await selectPaidPlanAndCheckout(page, orgId, p.orgPlan);
    await fillPayment(page, SUCCESS_PAN);
    await page.getByTestId('checkout-confirm').click();
    await skipTeamAndCompleteViaUi(page, orgId);
    await assertJourney(page, orgId, {
      next_action: 'enter_workspace',
      access_tier: 'operational',
    });
  });

  test('Owner decline then retry success at checkout', async ({ page }) => {
    const p = loadPersonas();
    await login(page, p.owner);
    const orgId = await createOrganizationViaUi(page, 'Label Decline 053');
    await selectPaidPlanAndCheckout(page, orgId, p.orgPlan);
    await fillPayment(page, DECLINED_PAN);
    await page.getByTestId('checkout-confirm').click();
    await expect(page.getByTestId('checkout-result')).toBeVisible({ timeout: 45_000 });
    await page.getByTestId('checkout-retry').click();
    await expect(page.getByTestId('checkout-payment')).toBeVisible({ timeout: 45_000 });
    await fillPayment(page, SUCCESS_PAN);
    await page.getByTestId('checkout-confirm').click();
    await skipTeamAndCompleteViaUi(page, orgId);
    await assertJourney(page, orgId, {
      next_action: 'enter_workspace',
      access_tier: 'operational',
    });
  });

  test('Owner trial path (trial → team skip → complete)', async ({ page }) => {
    const p = loadPersonas();
    await login(page, p.owner);
    const orgId = await createOrganizationViaUi(page, 'Label Trial 053');
    await expect(page.getByTestId('journey-trial')).toBeVisible({ timeout: 45_000 });
    await page.getByTestId('journey-trial').click();
    await page.waitForURL(new RegExp(`/subscriptions/trial\\?.*organization_id=${orgId}`), {
      timeout: 60_000,
    });
    await expect(page.locator('.plan-card').first()).toBeVisible({ timeout: 45_000 });
    await page.locator('.plan-card button').first().click();
    await page.locator('form button[type="submit"]').click();
    await skipTeamAndCompleteViaUi(page, orgId);
    await assertJourney(page, orgId, {
      next_action: 'enter_workspace',
      access_tier: 'operational',
    });
  });

  test('Invited viewer wait_for_owner while owner has not finished plan', async ({ page }) => {
    const p = loadPersonas();
    const fixture = await fixtureUnpaidInvite(page, p.owner, p.invitedViewer.email);
    await login(page, p.invitedViewer);
    const orgId = await acceptInviteViaUi(page, fixture.inviteToken);
    expect(orgId).toBe(fixture.orgId);
    await expect(page.getByTestId('org-onboarding-page')).toBeVisible({ timeout: 45_000 });
    await expect(page.getByTestId('journey-wait-owner')).toBeVisible({ timeout: 45_000 });
    await expect(page.getByTestId('journey-plan')).toHaveCount(0);
    await expect(page.getByTestId('journey-choose-plan')).toHaveCount(0);
    await assertJourney(page, orgId, {
      next_action: 'wait_for_owner',
      access_tier: 'onboarding',
    });
  });

  test('Invited viewer enter_workspace after owner completes journey', async ({ page }) => {
    const p = loadPersonas();
    await login(page, p.owner);
    const orgId = await createOrganizationViaUi(page, 'Viewer Ready 053');
    await selectPaidPlanAndCheckout(page, orgId, p.orgPlan);
    await fillPayment(page, SUCCESS_PAN);
    await page.getByTestId('checkout-confirm').click();
    await skipTeamAndCompleteViaUi(page, orgId);

    const headers = await authHeaders(page, orgId);
    const inviteRes = await page.request.post(`${API}/organizations/${orgId}/invitations`, {
      headers,
      data: { email: p.invitedViewer.email, role_codes: ['viewer'], ttl_days: 7 },
    });
    expect(inviteRes.ok(), `invite → ${inviteRes.status()}`).toBeTruthy();
    const inviteBody = await inviteRes.json();
    expect(inviteBody.invite_token).toBeTruthy();

    await login(page, p.invitedViewer);
    const joinedOrgId = await acceptInviteViaUi(page, inviteBody.invite_token);
    expect(joinedOrgId).toBe(orgId);
    await expect(page.getByTestId('journey-enter-workspace')).toBeVisible({ timeout: 45_000 });
    await expect(page.getByTestId('journey-choose-plan')).toHaveCount(0);
    await expect(page.getByTestId('journey-complete-submit')).toHaveCount(0);
    await page.getByTestId('journey-enter-hub').click();
    await page.waitForURL(new RegExp(`/organizations/${orgId}(/|$|\\?)`), { timeout: 60_000 });
    await assertJourney(page, orgId, {
      next_action: 'enter_workspace',
      access_tier: 'operational',
    });
  });
});
