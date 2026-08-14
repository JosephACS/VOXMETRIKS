import { test, expect, type APIRequestContext, type Page } from '@playwright/test';
import { loginAdmin, loginAs, logout } from '../fixtures/auth';

const API = 'http://127.0.0.1:8000/api/v1';
const AUTH_KEY = 'voxmetrik_auth_token';
const RETURN_URL_KEY = 'voxmetriks_return_url';
const SPACE_KEY = 'voxmetriks_active_space_v1';
/** Satisfies the shared account policy (>= 8 chars, not a shipped seed password). */
const STRONG_PASSWORD = 'secret1234';

const VIEWPORTS = [
  { name: 'desktop', width: 1366, height: 768 },
  { name: 'mobile', width: 390, height: 844 },
] as const;

interface VerifiedUser {
  email: string;
  username: string;
  userId: number;
  token: string;
}

function bearer(token: string): Record<string, string> {
  return { Authorization: `Bearer ${token}` };
}

async function openRegister(page: Page): Promise<void> {
  await page.goto('/login');
  await page.getByRole('tab', { name: /crear cuenta|sign up|register/i }).click();
}

async function sessionToken(page: Page): Promise<string> {
  const token = await page.evaluate(
    (key) => localStorage.getItem(key) ?? sessionStorage.getItem(key),
    AUTH_KEY,
  );
  expect(token, 'authenticated page must hold a session token').toBeTruthy();
  return token as string;
}

async function bootstrapSpaces(
  request: APIRequestContext,
  token: string,
): Promise<{ key: string; display_name: string }[]> {
  const res = await request.get(`${API}/session/bootstrap`, { headers: bearer(token) });
  expect(res.ok(), 'session bootstrap must succeed').toBeTruthy();
  const body = (await res.json()) as { spaces: { key: string; display_name: string }[] };
  return body.spaces;
}

/** Registers through the API and verifies with the dev channel code. */
async function createVerifiedUser(
  request: APIRequestContext,
  tag: string,
): Promise<VerifiedUser> {
  const stamp = `${Date.now()}${Math.floor(Math.random() * 1000)}`;
  const email = `vx_${tag}_${stamp}@voxmetrik.io`;
  const username = `vx${tag}${stamp}`.slice(0, 24);
  const registered = await request.post(`${API}/users/register`, {
    data: { username, email, password: STRONG_PASSWORD },
  });
  expect(registered.ok(), 'register must succeed').toBeTruthy();
  const code = (await registered.json()).dev_code as string;
  expect(code, 'the dev verification channel must be enabled for e2e').toMatch(/^\d{6}$/);

  const verified = await request.post(`${API}/users/verify-email`, {
    data: { email, code },
  });
  expect(verified.ok(), 'verify-email must succeed').toBeTruthy();
  const payload = (await verified.json()) as { token: string; user: { id: number } };
  return { email, username, userId: payload.user.id, token: payload.token };
}

async function apiLogin(
  request: APIRequestContext,
  login: string,
  password: string,
): Promise<string> {
  const res = await request.post(`${API}/users/login`, {
    data: { login, password, remember: true },
  });
  expect(res.ok(), `login for ${login} must succeed`).toBeTruthy();
  return (await res.json()).token as string;
}

for (const vp of VIEWPORTS) {
  test.describe(`050 identity first access ${vp.name}`, () => {
    test.use({ viewport: { width: vp.width, height: vp.height } });

    test('register form keeps confirmation and drops the favorite genre', async ({ page }) => {
      await openRegister(page);
      await expect(page.locator('#username')).toBeVisible();
      await expect(page.locator('#reg-email')).toBeVisible();
      await expect(page.locator('#reg-password')).toBeVisible();
      await expect(page.locator('#reg-password-confirm')).toBeVisible();
      await expect(page.locator('#genre')).toHaveCount(0);
    });

    test('register rejects short and shipped seed passwords', async ({ page }) => {
      await openRegister(page);
      await page.locator('#username').fill(`qa${vp.name}`);
      await page.locator('#reg-email').fill(`qa_${vp.name}@voxmetrik.io`);

      await page.locator('#reg-password').fill('short12');
      await page.locator('#reg-password-confirm').fill('short12');
      await page.locator('button.submit-btn[type="submit"]').click();
      await expect(page.getByText(/al menos 8|at least 8/i)).toBeVisible();

      await page.locator('#reg-password').fill('demo123');
      await page.locator('#reg-password-confirm').fill('demo123');
      await page.locator('button.submit-btn[type="submit"]').click();
      await expect(page.getByText(/demasiado común|too common/i)).toBeVisible();
      await expect(page).toHaveURL(/\/login/);
    });

    test('register from the UI shows the dev code and verification reaches first access', async ({
      page,
    }) => {
      const stamp = `${Date.now()}`;
      const email = `ui_${vp.name}_${stamp}@voxmetrik.io`;
      const username = `ui${vp.name}${stamp}`.slice(0, 24);

      await openRegister(page);
      await page.locator('#username').fill(username);
      await page.locator('#reg-email').fill(email);
      await page.locator('#reg-password').fill(STRONG_PASSWORD);
      await page.locator('#reg-password-confirm').fill(STRONG_PASSWORD);

      const registered = page.waitForResponse(
        (res) => res.url().includes('/users/register') && res.request().method() === 'POST',
      );
      await page.locator('button.submit-btn[type="submit"]').click();
      const code = ((await (await registered).json()).dev_code ?? '') as string;
      expect(code, 'the dev verification channel must be enabled for e2e').toMatch(/^\d{6}$/);

      await expect(page.locator('#code')).toBeVisible({ timeout: 20_000 });
      // devVerificationChannel is on for local builds, so the code is surfaced in the UI.
      await expect(page.locator('.dev-code-banner')).toContainText(code);

      await page.locator('#code').fill(code);
      await page.locator('button.submit-btn[type="submit"]').click();
      await page.waitForURL(/\/(welcome|discover|account\/profiles)/, { timeout: 45_000 });
      await expect(page).not.toHaveURL(/\/login/);
    });

    test('recovery form keeps the email and asks for the code', async ({ page }) => {
      await page.goto('/login');
      await page.getByRole('button', { name: /olvidaste|forgot/i }).click();
      await page.locator('#forgot-email').fill('demo@voxmetrik.io');
      await page.locator('button.submit-btn').click();
      await expect(page.locator('#reset-email')).toHaveValue('demo@voxmetrik.io');
      await expect(page.locator('#reset-code')).toBeVisible();
    });

    test('unsafe returnUrl is ignored', async ({ page }) => {
      await page.goto('/login?returnUrl=https://evil.example/phish');
      await page.locator('#loginId').fill('demo');
      await page.locator('#password').fill('demo123');
      await page.locator('button.submit-btn[type="submit"]').click();
      await page.waitForURL(/\/(discover|welcome|workpanel)/, { timeout: 45_000 });
      await expect(page).not.toHaveURL(/evil/);
    });

    test('organization invitation acceptance is reachable without prior membership', async ({
      page,
    }) => {
      const target = '/invitations/accept?token=qa-org-invite-token';
      await page.goto(target);
      await page.locator('#loginId').fill('demo');
      await page.locator('#password').fill('demo123');
      await page.locator('button.submit-btn[type="submit"]').click();
      await page.waitForURL(/\/invitations\/accept/, { timeout: 45_000 });
      await expect(page.getByTestId('app-shell')).toBeVisible();
      await expect(page.locator('input[name="token"]')).toHaveValue('qa-org-invite-token');
      await expect(page).not.toHaveURL(/token=/);
      const leftover = await page.evaluate((key) => sessionStorage.getItem(key), RETURN_URL_KEY);
      expect(leftover, 'returnUrl must be consumed once the destination is reached').toBeNull();
    });

    test('artist invitation acceptance is reachable without an artist space', async ({ page }) => {
      const target = '/artist-invitations/accept?token=qa-artist-invite-token';
      await page.goto(target);
      await page.locator('#loginId').fill('demo');
      await page.locator('#password').fill('demo123');
      await page.locator('button.submit-btn[type="submit"]').click();
      await page.waitForURL(/\/artist-invitations\/accept/, { timeout: 45_000 });
      await expect(page.getByTestId('app-shell')).toBeVisible();
      await expect(page.locator('input[formcontrolname="token"]')).toHaveValue(
        'qa-artist-invite-token',
      );
      await expect(page).not.toHaveURL(/token=/);
    });

    test('admin with several spaces gets a working space selector', async ({ page, request }) => {
      await loginAdmin(page);
      const spaces = await bootstrapSpaces(request, await sessionToken(page));
      expect(spaces.length, 'admin must own more than one space').toBeGreaterThan(1);

      const selector = page.getByTestId('space-selector');
      await expect(selector).toBeVisible();
      await selector.getByRole('button').first().click();
      const list = page.getByRole('listbox');
      await expect(list).toBeVisible();
      expect(await list.getByRole('option').count()).toBeGreaterThan(1);
    });

    test('bootstrap failure never invents spaces', async ({ page }) => {
      await page.route('**/session/bootstrap', (route) => route.abort());
      await page.goto('/login');
      await page.locator('#loginId').fill('demo');
      await page.locator('#password').fill('demo123');
      await page.locator('button.submit-btn[type="submit"]').click();

      await expect(page.getByTestId('bootstrap-retry')).toBeVisible({ timeout: 30_000 });
      await expect(page).toHaveURL(/\/login/);
      await expect(page.getByTestId('app-shell')).toHaveCount(0);
      const stored = await page.evaluate((key) => localStorage.getItem(key), SPACE_KEY);
      expect(stored, 'no space may be persisted without a manifest').toBeNull();
    });

    test('logout leaves no private client state for the next account', async ({ page }) => {
      await page.goto('/login?returnUrl=/history');
      await page.locator('#loginId').fill('demo');
      await page.locator('#password').fill('demo123');
      await page.locator('button.submit-btn[type="submit"]').click();
      await page.waitForURL(/\/(history|discover|welcome|account\/profiles)/, { timeout: 45_000 });

      await logout(page);
      const leftovers = await page.evaluate(
        ([returnKey, spaceKey, authKey]) => ({
          returnUrl: sessionStorage.getItem(returnKey),
          space: localStorage.getItem(spaceKey),
          token: localStorage.getItem(authKey) ?? sessionStorage.getItem(authKey),
        }),
        [RETURN_URL_KEY, SPACE_KEY, AUTH_KEY],
      );
      expect(leftovers.returnUrl).toBeNull();
      expect(leftovers.space).toBeNull();
      expect(leftovers.token).toBeNull();

      await loginAdmin(page);
      await expect(page).not.toHaveURL(/\/login/);
    });

    test('membership revocation drops the organization space without leaking it', async ({
      page,
      request,
    }) => {
      const member = await createVerifiedUser(request, `rev${vp.name}`);
      const adminToken = await apiLogin(request, 'admin', 'admin123');
      const orgName = `QA Revocation ${Date.now()}`;

      const created = await request.post(`${API}/organizations`, {
        headers: bearer(adminToken),
        data: { display_name: orgName, organization_type: 'label', activate: false },
      });
      expect(created.ok(), 'organization creation must succeed').toBeTruthy();
      const orgId = (await created.json()).organization.id as number;

      const invited = await request.post(`${API}/organizations/${orgId}/invitations`, {
        headers: bearer(adminToken),
        data: { email: member.email, role_codes: ['analyst'], ttl_days: 7 },
      });
      expect(invited.ok(), 'invitation creation must succeed').toBeTruthy();
      const inviteToken = (await invited.json()).invite_token as string;

      const accepted = await request.post(`${API}/invitations/${inviteToken}/accept`, {
        headers: bearer(member.token),
      });
      expect(accepted.ok(), 'invitation acceptance must succeed').toBeTruthy();

      const withOrg = await bootstrapSpaces(request, member.token);
      expect(withOrg.some((s) => s.key === `organization:${orgId}`)).toBeTruthy();

      await loginAs(page, member.email, STRONG_PASSWORD);
      await expect(page.getByText(orgName).first()).toBeVisible({ timeout: 20_000 });

      const members = await request.get(`${API}/organizations/${orgId}/members`, {
        headers: bearer(adminToken),
      });
      expect(members.ok(), 'member listing must succeed').toBeTruthy();
      const membership = ((await members.json()).items as { id: number; user_id: number }[]).find(
        (m) => m.user_id === member.userId,
      );
      expect(membership, 'the invited member must exist before revocation').toBeTruthy();

      const removed = await request.post(
        `${API}/organizations/${orgId}/members/${membership!.id}/remove`,
        { headers: bearer(adminToken) },
      );
      expect(removed.ok(), 'member removal must succeed').toBeTruthy();

      const afterRevocation = await bootstrapSpaces(request, member.token);
      expect(afterRevocation.some((s) => s.key === `organization:${orgId}`)).toBeFalsy();

      await page.goto('/discover');
      await expect(page.getByTestId('app-shell')).toBeVisible({ timeout: 20_000 });
      await expect(page.getByText(orgName)).toHaveCount(0);
    });
  });
}
