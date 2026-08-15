/**
 * Seed Spec 051 personas against the isolated API.
 * Writes credentials JSON for Playwright. Fail-closed on invite/org failures.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { API_BASE, TEMP_ROOT } from './051-isolated-db.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(TEMP_ROOT, 'personas.json');
const STRONG = 'Secret051!pass';

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
  const email = `vx051_${tag}_${stamp}@voxmetrik.io`;
  const username = `vx051${tag}${stamp}`.slice(0, 24);
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

async function login(loginId, password) {
  const res = await fetch(`${API_BASE}/api/v1/users/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ login: loginId, password, remember: true }),
  });
  const body = await json(res);
  return body.token;
}

async function createNewArtistRequest(token, displayName) {
  const res = await fetch(`${API_BASE}/api/v1/artist-access/requests`, {
    method: 'POST',
    headers: bearer(token),
    body: JSON.stringify({
      request_type: 'create_new',
      proposed_display_name: displayName,
      proposed_role: 'owner',
      relationship_type: 'artist_self',
      evidence_url: 'https://example.com/evidence/051',
      evidence_note: 'E2E Spec 051 evidence note for create_new',
      accuracy_attested: true,
    }),
  });
  return json(res);
}

async function platformApprove(adminToken, requestId) {
  const res = await fetch(`${API_BASE}/api/v1/platform/artist-requests/${requestId}/approve`, {
    method: 'POST',
    headers: bearer(adminToken),
    body: JSON.stringify({}),
  });
  return json(res);
}

async function listMine(token) {
  const res = await fetch(`${API_BASE}/api/v1/artist-space/mine`, {
    headers: bearer(token),
  });
  return json(res);
}

async function inviteMember(ownerToken, artistProfileId, email, role) {
  const res = await fetch(`${API_BASE}/api/v1/artist-space/${artistProfileId}/invitations`, {
    method: 'POST',
    headers: bearer(ownerToken),
    body: JSON.stringify({ email, role }),
  });
  return json(res);
}

async function acceptInvite(token, invitationToken) {
  const res = await fetch(`${API_BASE}/api/v1/artist-invitations/accept`, {
    method: 'POST',
    headers: bearer(token),
    body: JSON.stringify({ token: invitationToken }),
  });
  return json(res);
}

async function startOrgTrial(managerToken, orgId) {
  const headers = { ...bearer(managerToken), 'X-Organization-Id': String(orgId) };
  const plansBody = await json(
    await fetch(`${API_BASE}/api/v1/plans?limit=100&status=active`, {
      headers: bearer(managerToken),
    }),
  );
  const plans = plansBody.items || plansBody || [];
  const plan = plans[0];
  if (!plan?.id) throw new Error(`FAIL-CLOSED: no active plans for trial: ${JSON.stringify(plansBody).slice(0, 300)}`);

  const pricesBody = await json(
    await fetch(`${API_BASE}/api/v1/plans/${plan.id}/prices`, {
      headers: bearer(managerToken),
    }),
  );
  const prices = Array.isArray(pricesBody) ? pricesBody : pricesBody.items || [];
  const price = prices.find((p) => p.status === 'active') || prices[0];
  if (!price?.id) {
    throw new Error(`FAIL-CLOSED: plan ${plan.id} has no price: ${JSON.stringify(pricesBody).slice(0, 300)}`);
  }

  return json(
    await fetch(`${API_BASE}/api/v1/subscriptions/trial`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        organization_id: Number(orgId),
        plan_id: Number(plan.id),
        plan_price_id: Number(price.id),
        billing_currency: String(price.currency || 'USD').slice(0, 3),
        trial_days: 14,
        activation_source: 'trial',
      }),
    }),
  );
}

async function ensureOrgWithArtists(managerToken) {
  const created = await json(
    await fetch(`${API_BASE}/api/v1/organizations`, {
      method: 'POST',
      headers: bearer(managerToken),
      body: JSON.stringify({
        display_name: `Label 051 ${Date.now()}`,
        organization_type: 'label',
      }),
    }),
  );
  const orgId = created.id || created.organization_id || created.organization?.id;
  if (!orgId) throw new Error(`org create missing id: ${JSON.stringify(created)}`);

  await startOrgTrial(managerToken, orgId);

  const headers = { ...bearer(managerToken), 'X-Organization-Id': String(orgId) };
  const artists = [];
  for (const name of ['Act One 051', 'Act Two 051']) {
    const a = await json(
      await fetch(`${API_BASE}/api/v1/artists`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ display_name: name }),
      }),
    );
    const artistId = a.id || a.artist_profile_id || a.profile?.id;
    if (!artistId) throw new Error(`artist create missing id: ${JSON.stringify(a)}`);
    const activated = await json(
      await fetch(`${API_BASE}/api/v1/artists/${artistId}/activate`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ reason: 'Spec 051 E2E seed activate' }),
      }),
    );
    artists.push({
      id: artistId,
      display_name: activated.display_name || name,
      status: activated.status || 'active',
    });
  }
  if (artists.length < 2) throw new Error('label seed must create two artists');
  return { orgId, artists };
}

async function main() {
  fs.mkdirSync(TEMP_ROOT, { recursive: true });

  let platformAdmin;
  try {
    const token = await login('admin', 'admin123');
    platformAdmin = { email: 'admin', username: 'admin', password: 'admin123', token };
  } catch (err) {
    throw new Error(`FAIL-CLOSED: seeded admin login required on temp DB: ${err.message}`);
  }

  const listener = await registerVerified('lstn');
  const owner = await registerVerified('ownr');
  const administrator = await registerVerified('admn');
  const collaborator = await registerVerified('coll');
  const reader = await registerVerified('read');
  const labelManager = await registerVerified('labm');

  const req = await createNewArtistRequest(owner.token, `Owner Band ${Date.now()}`);
  const requestId = req.id || req.request_id;
  if (!requestId) throw new Error(`create_new missing id: ${JSON.stringify(req)}`);
  const approved = await platformApprove(platformAdmin.token, requestId);
  let profileId =
    approved.profile?.id ||
    approved.profile?.artist_profile_id ||
    null;
  if (!profileId) {
    const mine = await listMine(owner.token);
    const items = Array.isArray(mine) ? mine : mine?.items || [];
    profileId = items[0]?.artist_profile_id || items[0]?.id || null;
  }
  if (!profileId) throw new Error(`approve did not yield profile: ${JSON.stringify(approved)}`);

  async function inviteAndAccept(user, role) {
    const inv = await inviteMember(owner.token, profileId, user.email, role);
    const tokenValue = inv.invite_token || inv.token || inv.invitation_token;
    if (!tokenValue) {
      throw new Error(`invitation token missing for ${role}: ${JSON.stringify(inv)}`);
    }
    await acceptInvite(user.token, tokenValue);
  }

  await inviteAndAccept(administrator, 'administrator');
  await inviteAndAccept(collaborator, 'member');
  await inviteAndAccept(reader, 'reader');

  const label = await ensureOrgWithArtists(labelManager.token);

  const personas = {
    apiBase: `${API_BASE}/api/v1`,
    password: STRONG,
    platformAdmin,
    listener,
    owner: { ...owner, artistProfileId: profileId },
    administrator: { ...administrator, artistProfileId: profileId },
    collaborator: { ...collaborator, artistProfileId: profileId },
    reader: { ...reader, artistProfileId: profileId },
    labelManager: { ...labelManager, orgId: label.orgId, artists: label.artists },
  };
  fs.writeFileSync(OUT, JSON.stringify(personas, null, 2));
  console.log(`[051-seed] wrote ${OUT}`);
  console.log(`[051-seed] artistProfileId=${profileId} orgId=${label.orgId}`);
}

main().catch((err) => {
  console.error('[051-seed] FAILED', err);
  process.exit(1);
});
