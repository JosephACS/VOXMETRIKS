/**
 * Seed Spec 056 professional closure personas against the isolated API.
 * Prefer warehouse admin (identity staff → CRM hub) because DuckDB is locked by uvicorn.
 */
import fs from 'node:fs';
import path from 'node:path';
import { API_BASE, TEMP_ROOT } from './056-isolated-db.mjs';

const OUT = path.join(TEMP_ROOT, 'personas.json');
const STRONG = 'Secret056!pass';

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
  const email = `vx056_${tag}_${stamp}@voxmetrik.io`;
  const username = `vx056${tag}${stamp}`.slice(0, 24);
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

async function resolveOwner() {
  try {
    const admin = await loginExisting('admin', 'admin123');
    if ((admin.role || '').toLowerCase() !== 'admin') {
      throw new Error(`admin login role=${admin.role}`);
    }
    console.log('[056-seed] owner via admin/admin123 (CRM staff shell)');
    return admin;
  } catch (err) {
    console.warn(`[056-seed] admin/admin123 unavailable: ${err}`);
  }
  const owner = await registerVerified('owner');
  console.warn(
    '[056-seed] WARNING: registered owner without sales_manager (DuckDB locked); CRM may be hidden',
  );
  return owner;
}

async function main() {
  const dbPath = process.env.DB_PATH;
  if (!dbPath || !String(dbPath).includes('voxmetrik-056-e2e')) {
    throw new Error('FAIL-CLOSED: seed requires isolated DB_PATH under voxmetrik-056-e2e');
  }

  const owner = await resolveOwner();
  const restricted = await registerVerified('viewer');
  // Restricted stays personal-only (no org invite) so commercial hubs stay hidden.

  const orgLabel = `Closure 056 Org ${Date.now()}`;
  const orgRes = await fetch(`${API_BASE}/api/v1/organizations`, {
    method: 'POST',
    headers: bearer(owner.token),
    body: JSON.stringify({
      display_name: orgLabel,
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
        activation_source: 'e2e_056_seed',
      }),
    }),
  );

  const out = {
    apiBase: API_BASE,
    orgId,
    orgLabel,
    owner: { ...owner, orgId },
    restricted: { ...restricted },
  };
  fs.mkdirSync(TEMP_ROOT, { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(out, null, 2), 'utf8');
  console.log(`[056-seed] wrote ${OUT}`);
  console.log(`[056-seed] owner=${owner.username} restricted=${restricted.username} org=${orgId}`);
}

main().catch((err) => {
  console.error('[056-seed] FAILED', err);
  process.exit(1);
});
