/**
 * Seed Spec 054 navigation personas against the isolated API.
 * Fixture mutations only — Playwright asserts UI navigation.
 */
import fs from 'node:fs';
import path from 'node:path';
import { API_BASE, TEMP_ROOT } from './054-isolated-db.mjs';

const OUT = path.join(TEMP_ROOT, 'personas.json');
const STRONG = 'Secret054!pass';

function bearer(token, orgId) {
  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
  if (orgId != null) headers['X-Organization-Id'] = String(orgId);
  return headers;
}

async function json(res) {
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(`${res.status} ${res.url} ${JSON.stringify(body).slice(0, 400)}`);
  }
  return body;
}

async function registerVerified(tag) {
  const stamp = `${Date.now()}${Math.floor(Math.random() * 1000)}`;
  const email = `vx054_${tag}_${stamp}@voxmetrik.io`;
  const username = `vx054${tag}${stamp}`.slice(0, 24);
  const registered = await fetch(`${API_BASE}/api/v1/users/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password: STRONG }),
  });
  const regBody = await json(registered);
  const code = regBody.dev_code;
  if (!/^\d{6}$/.test(String(code || ''))) {
    throw new Error(`dev_code missing for ${email} — E2E=1 required`);
  }
  const verified = await fetch(`${API_BASE}/api/v1/users/verify-email`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, code }),
  });
  const payload = await json(verified);
  return {
    email,
    username,
    password: STRONG,
    userId: payload.user?.id,
    token: payload.token,
  };
}

async function loginExisting(loginId, password) {
  const res = await fetch(`${API_BASE}/api/v1/users/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ login: loginId, password, remember: true }),
  });
  const body = await json(res);
  return {
    email: body.user?.email || loginId,
    username: body.user?.username || loginId,
    password,
    userId: body.user?.id,
    token: body.token,
    role: body.user?.role,
  };
}

async function resolveOrgPlan(token, orgId) {
  const plansRes = await fetch(`${API_BASE}/api/v1/plans?status=active&limit=50`, {
    headers: bearer(token, orgId),
  });
  const plansBody = await json(plansRes);
  const plans = plansBody.items || plansBody || [];
  const preferred =
    plans.find((p) => String(p.code || '').toLowerCase() === 'starter') || plans[0];
  if (!preferred?.id) throw new Error('no active commercial plan from GET /plans');
  const pricesRes = await fetch(`${API_BASE}/api/v1/plans/${preferred.id}/prices`, {
    headers: bearer(token, orgId),
  });
  const pricesBody = await json(pricesRes);
  const prices = Array.isArray(pricesBody) ? pricesBody : pricesBody.items || [];
  const monthly =
    prices.find(
      (p) =>
        String(p.status || '').toLowerCase() === 'active' &&
        String(p.billing_period || '').toLowerCase() === 'monthly',
    ) || prices.find((p) => String(p.status || '').toLowerCase() === 'active');
  if (!monthly?.id) throw new Error(`no active price for plan ${preferred.code}`);
  return {
    plan_id: Number(preferred.id),
    plan_price_id: Number(monthly.id),
    billing_currency: String(monthly.currency || 'USD'),
  };
}

async function inviteAndAccept(ownerToken, orgId, invitee, roleCodes) {
  const inviteRes = await fetch(`${API_BASE}/api/v1/organizations/${orgId}/invitations`, {
    method: 'POST',
    headers: bearer(ownerToken, orgId),
    body: JSON.stringify({
      email: invitee.email,
      role_codes: roleCodes,
      ttl_days: 7,
    }),
  });
  const inviteBody = await json(inviteRes);
  const inviteToken = inviteBody.invite_token;
  if (!inviteToken) throw new Error(`invite_token missing for ${invitee.email}`);
  await json(
    await fetch(`${API_BASE}/api/v1/invitations/${encodeURIComponent(inviteToken)}/accept`, {
      method: 'POST',
      headers: bearer(invitee.token),
    }),
  );
}

async function main() {
  const dbPath = process.env.DB_PATH;
  if (!dbPath || !String(dbPath).includes('voxmetrik-054-e2e')) {
    throw new Error('FAIL-CLOSED: seed requires isolated DB_PATH under voxmetrik-054-e2e');
  }

  const owner = await registerVerified('owner');
  const analyst = await registerVerified('analyst');
  const billing = await registerVerified('billing');
  const viewer = await registerVerified('viewer');

  const orgRes = await fetch(`${API_BASE}/api/v1/organizations`, {
    method: 'POST',
    headers: bearer(owner.token),
    body: JSON.stringify({
      display_name: 'Nav Matrix 054',
      organization_type: 'label',
      timezone: 'UTC',
      default_currency: 'USD',
      activate: true,
    }),
  });
  const orgBody = await json(orgRes);
  const orgId = orgBody.organization?.id;
  if (!orgId) throw new Error('organization id missing after create');

  const plan = await resolveOrgPlan(owner.token, orgId);
  await json(
    await fetch(`${API_BASE}/api/v1/subscriptions/trial`, {
      method: 'POST',
      headers: bearer(owner.token, orgId),
      body: JSON.stringify({
        organization_id: orgId,
        plan_id: plan.plan_id,
        plan_price_id: plan.plan_price_id,
        billing_currency: plan.billing_currency,
        trial_days: 14,
        activation_source: 'e2e_054_seed',
      }),
    }),
  );

  await inviteAndAccept(owner.token, orgId, analyst, ['analyst']);
  await inviteAndAccept(owner.token, orgId, billing, ['billing_manager']);
  await inviteAndAccept(owner.token, orgId, viewer, ['viewer']);

  const engineer = await loginExisting('engineer', 'engineer123');
  const platformAdmin = await loginExisting('admin', 'admin123');

  // Artist: register + claim if endpoint allows; otherwise personal-only artist path still tested via unit matrix.
  const artistUser = await registerVerified('artist');
  let artistClaimed = false;
  try {
    const claim = await fetch(`${API_BASE}/api/v1/artist-space/claim`, {
      method: 'POST',
      headers: bearer(artistUser.token),
      body: JSON.stringify({ display_name: `Artist 054 ${Date.now()}` }),
    });
    if (claim.ok) {
      artistClaimed = true;
      await claim.json().catch(() => ({}));
    }
  } catch {
    artistClaimed = false;
  }

  // Capture hydrated membership permissions for E2E diagnostics / assertions.
  async function loadMembership(token, orgId) {
    const res = await fetch(`${API_BASE}/api/v1/organizations/${orgId}/activate`, {
      method: 'POST',
      headers: bearer(token, orgId),
    });
    const body = await json(res);
    return {
      permissions: body.permissions || [],
      roles: body.roles || [],
      subscription_access: body.subscription_access || null,
    };
  }

  const ownerCtx = await loadMembership(owner.token, orgId);
  const analystCtx = await loadMembership(analyst.token, orgId);
  const billingCtx = await loadMembership(billing.token, orgId);
  const viewerCtx = await loadMembership(viewer.token, orgId);

  const out = {
    apiBase: API_BASE,
    password: STRONG,
    orgId,
    owner: { ...owner, orgId, ...ownerCtx },
    analyst: { ...analyst, orgId, ...analystCtx },
    billing: { ...billing, orgId, ...billingCtx },
    viewer: { ...viewer, orgId, ...viewerCtx },
    engineer,
    platformAdmin,
    artist: { ...artistUser, claimed: artistClaimed },
  };
  fs.mkdirSync(TEMP_ROOT, { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(out, null, 2), 'utf8');
  console.log(`[054-seed] wrote ${OUT}`);
  console.log(
    `[054-seed] orgId=${orgId} artistClaimed=${artistClaimed} owner.report.view=${ownerCtx.permissions.includes('report.view')} analyst.report.view=${analystCtx.permissions.includes('report.view')} owner.tier=${ownerCtx.subscription_access?.tier} analyst.tier=${analystCtx.subscription_access?.tier}`,
  );
}

main().catch((err) => {
  console.error('[054-seed] FAILED', err);
  process.exit(1);
});
