/**
 * Seed Spec 053 personas against the isolated API.
 * Owner + pending invite for viewer on a shared unpaid org.
 * Invitation accept/activate is exercised by Playwright UI (not here).
 */
import fs from 'node:fs';
import path from 'node:path';
import { API_BASE, TEMP_ROOT } from './053-isolated-db.mjs';

const OUT = path.join(TEMP_ROOT, 'personas.json');
const STRONG = 'Secret053!pass';

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
  const email = `vx053_${tag}_${stamp}@voxmetrik.io`;
  const username = `vx053${tag}${stamp}`.slice(0, 24);
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
    plan_display_name: String(preferred.display_name || preferred.code),
  };
}

async function main() {
  const dbPath = process.env.DB_PATH;
  if (!dbPath || !String(dbPath).includes('voxmetrik-053-e2e')) {
    throw new Error('FAIL-CLOSED: seed requires isolated DB_PATH under voxmetrik-053-e2e');
  }

  const owner = await registerVerified('owner');
  const invitedViewer = await registerVerified('viewer');

  const orgRes = await fetch(`${API_BASE}/api/v1/organizations`, {
    method: 'POST',
    headers: bearer(owner.token),
    body: JSON.stringify({
      display_name: 'Shared Journey 053',
      organization_type: 'label',
      timezone: 'UTC',
      default_currency: 'USD',
      activate: true,
    }),
  });
  const orgBody = await json(orgRes);
  const sharedOrgId = orgBody.organization?.id;
  if (!sharedOrgId) throw new Error('organization id missing after create');

  const inviteRes = await fetch(`${API_BASE}/api/v1/organizations/${sharedOrgId}/invitations`, {
    method: 'POST',
    headers: bearer(owner.token),
    body: JSON.stringify({
      email: invitedViewer.email,
      role_codes: ['viewer'],
      ttl_days: 7,
    }),
  });
  const inviteBody = await json(inviteRes);
  const inviteToken = inviteBody.invite_token;
  if (!inviteToken) {
    throw new Error(
      'invite_token missing — E2E=1 or ORGANIZATION_INVITATION_DELIVERY_MODE=local_once required',
    );
  }

  const plan = await resolveOrgPlan(owner.token);

  const catalogsRes = await fetch(`${API_BASE}/api/v1/organizations/catalogs`);
  const catalogs = await json(catalogsRes);
  if (!catalogs?.organization_types?.length) {
    throw new Error('organizations/catalogs returned empty organization_types');
  }

  const journeyRes = await fetch(
    `${API_BASE}/api/v1/organizations/${sharedOrgId}/journey`,
    { headers: bearer(owner.token) },
  );
  const journey = await json(journeyRes);
  if (!journey?.next_action) {
    throw new Error('journey read missing next_action');
  }

  const out = {
    apiBase: API_BASE,
    password: STRONG,
    owner,
    invitedViewer: { ...invitedViewer, orgId: sharedOrgId },
    sharedOrgId,
    orgPlan: plan,
    inviteToken,
    journeyNextAction: journey.next_action,
  };
  fs.mkdirSync(TEMP_ROOT, { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(out, null, 2), 'utf8');
  console.log(`[053-seed] wrote ${OUT}`);
  console.log(
    `[053-seed] owner=${owner.email} viewer=${invitedViewer.email} org=${sharedOrgId} journey=${journey.next_action} invite_pending=1`,
  );
}

main().catch((err) => {
  console.error('[053-seed] FAILED', err);
  process.exit(1);
});
