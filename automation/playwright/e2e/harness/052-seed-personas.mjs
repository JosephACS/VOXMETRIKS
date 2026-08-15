/**
 * Seed Spec 052 personas against the isolated API.
 * Writes credentials JSON for Playwright. Fail-closed on org provisioning.
 */
import fs from 'node:fs';
import path from 'node:path';
import { API_BASE, TEMP_ROOT } from './052-isolated-db.mjs';

const OUT = path.join(TEMP_ROOT, 'personas.json');
const STRONG = 'Secret052!pass';

function bearer(token) {
  return { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
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
  const email = `vx052_${tag}_${stamp}@voxmetrik.io`;
  const username = `vx052${tag}${stamp}`.slice(0, 24);
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

async function resolveOrgPlan(token) {
  const plansRes = await fetch(`${API_BASE}/api/v1/plans?status=active&limit=50`, {
    headers: bearer(token),
  });
  const plansBody = await json(plansRes);
  const plans = plansBody.items || plansBody || [];
  const preferred =
    plans.find((p) => String(p.code || '').toLowerCase() === 'starter') || plans[0];
  if (!preferred?.id) throw new Error('no active commercial plan from GET /plans');
  const pricesRes = await fetch(`${API_BASE}/api/v1/plans/${preferred.id}/prices`, {
    headers: bearer(token),
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
    billing_period: String(monthly.billing_period || 'monthly'),
    currency: String(monthly.currency || 'USD'),
    plan_code: String(preferred.code),
  };
}

async function main() {
  const dbPath = process.env.DB_PATH;
  if (!dbPath || !String(dbPath).includes('voxmetrik-052-e2e')) {
    throw new Error('FAIL-CLOSED: seed requires isolated DB_PATH under voxmetrik-052-e2e');
  }

  const personal = await registerVerified('pers');
  const orgOwner = await registerVerified('org');

  const orgRes = await fetch(`${API_BASE}/api/v1/organizations`, {
    method: 'POST',
    headers: bearer(orgOwner.token),
    body: JSON.stringify({
      display_name: 'Label Checkout 052',
      organization_type: 'label',
      timezone: 'UTC',
      default_currency: 'USD',
      activate: true,
    }),
  });
  const orgBody = await json(orgRes);
  const orgId = orgBody.organization?.id;
  if (!orgId) throw new Error('organization id missing after create');

  const plan = await resolveOrgPlan(orgOwner.token);

  const out = {
    apiBase: API_BASE,
    password: STRONG,
    personal,
    orgOwner: { ...orgOwner, orgId },
    orgPlan: plan,
  };
  fs.mkdirSync(TEMP_ROOT, { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(out, null, 2), 'utf8');
  console.log(`[052-seed] wrote ${OUT}`);
  console.log(`[052-seed] personal=${personal.email} org=${orgId} plan=${plan.plan_code}`);
}

main().catch((err) => {
  console.error('[052-seed] FAILED', err);
  process.exit(1);
});
