/**
 * Seed Spec 055 platform-admin persona against the isolated API.
 * Fixture mutations only — Playwright asserts UI journey + mutations.
 */
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { API_BASE, REPO_ROOT, TEMP_ROOT } from './055-isolated-db.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(TEMP_ROOT, 'personas.json');
const STRONG = 'Secret055!pass';

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
  const email = `vx055_${tag}_${stamp}@voxmetrik.io`;
  const username = `vx055${tag}${stamp}`.slice(0, 24);
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
    role: payload.user?.role,
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

function repositoryPython() {
  const candidate = path.join(
    REPO_ROOT,
    '.venv',
    process.platform === 'win32' ? 'Scripts' : 'bin',
    process.platform === 'win32' ? 'python.exe' : 'python',
  );
  if (fs.existsSync(candidate)) return candidate;
  return process.platform === 'win32' ? 'python.exe' : 'python3';
}

/**
 * Assign CRM platform_admin while API holds the DB when possible.
 * Prefer identity role=admin (copied warehouse admin) — this is the fallback path.
 */
function assignPlatformAdminRole(userId, dbPath) {
  const py = repositoryPython();
  const script = `
import os, sys
sys.path.insert(0, r${JSON.stringify(path.join(REPO_ROOT, 'apps', 'backend'))})
os.environ["DB_PATH"] = r${JSON.stringify(dbPath)}
import duckdb
from app.packages.platform_rbac.infrastructure.repository import assign_role
from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
conn = duckdb.connect(os.environ["DB_PATH"])
try:
    ensure_platform_rbac_tables(conn)
    assign_role(conn, user_id=int(${Number(userId)}), role_code="platform_admin", assigned_by=None)
    # Also elevate identity role so is_platform_admin() passes immediately.
    for table in ("app_user", "users"):
        try:
            conn.execute(f"UPDATE {table} SET role = 'admin' WHERE id = ?", [int(${Number(userId)})])
            break
        except Exception:
            continue
    print("ok")
finally:
    conn.close()
`;
  const result = spawnSync(py, ['-c', script], {
    cwd: path.join(REPO_ROOT, 'apps', 'backend'),
    encoding: 'utf8',
    env: { ...process.env, DB_PATH: dbPath },
  });
  if (result.status !== 0) {
    throw new Error(
      `assign platform_admin failed (DuckDB may be locked by API): ${result.stderr || result.stdout}`,
    );
  }
}

async function assertOverviewAuthorized(token) {
  const res = await fetch(`${API_BASE}/api/v1/platform-ops/overview`, {
    headers: bearer(token),
  });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`platform admin token cannot access overview: ${res.status}`);
  }
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`overview unexpected ${res.status}: ${body.slice(0, 300)}`);
  }
}

async function seedPendingArtistRequest(applicantToken) {
  const displayName = `E2E 055 Band ${Date.now()}`;
  const res = await fetch(`${API_BASE}/api/v1/artist-access/requests`, {
    method: 'POST',
    headers: bearer(applicantToken),
    body: JSON.stringify({
      request_type: 'create_new',
      proposed_display_name: displayName,
      proposed_role: 'owner',
      relationship_type: 'artist_self',
      evidence_url: 'https://example.com/evidence/055',
      evidence_note: 'E2E Spec 055 pending artist request',
      accuracy_attested: true,
    }),
  });
  const body = await json(res);
  const requestId = body.id || body.request_id || null;
  if (!requestId) {
    throw new Error('FAIL-CLOSED: pending artist request response has no id');
  }
  return {
    id: requestId,
    proposed_display_name: displayName,
  };
}

async function resolvePlatformAdmin(dbPath) {
  try {
    const admin = await loginExisting('admin', 'admin123');
    await assertOverviewAuthorized(admin.token);
    console.log('[055-seed] platformAdmin via admin/admin123');
    return admin;
  } catch (loginErr) {
    console.warn(`[055-seed] admin/admin123 unavailable: ${loginErr}`);
  }

  const registered = await registerVerified('padm');
  if (!registered.userId) {
    throw new Error('FAIL-CLOSED: registered platform admin missing userId');
  }
  assignPlatformAdminRole(registered.userId, dbPath);
  const elevated = await loginExisting(registered.email, registered.password);
  await assertOverviewAuthorized(elevated.token);
  console.log('[055-seed] platformAdmin via register + assign platform_admin');
  return elevated;
}

async function main() {
  const dbPath = process.env.DB_PATH;
  if (!dbPath || !String(dbPath).includes('voxmetrik-055-e2e')) {
    throw new Error('FAIL-CLOSED: seed requires isolated DB_PATH under voxmetrik-055-e2e');
  }

  const platformAdmin = await resolvePlatformAdmin(dbPath);

  const applicants = [
    await registerVerified('appl1'),
    await registerVerified('appl2'),
  ];
  const pendingArtistRequests = [];
  for (const applicant of applicants) {
    pendingArtistRequests.push(await seedPendingArtistRequest(applicant.token));
  }
  const applicant = applicants[0];
  const pendingArtistRequest = pendingArtistRequests[0];

  const out = {
    apiBase: API_BASE,
    password: STRONG,
    platformAdmin,
    applicant,
    pendingArtistRequest,
    pendingArtistRequests,
  };
  fs.mkdirSync(TEMP_ROOT, { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(out, null, 2), 'utf8');
  console.log(`[055-seed] wrote ${OUT}`);
  console.log(
    `[055-seed] platformAdmin=${platformAdmin.username} pendingRequests=${pendingArtistRequests.map((request) => request.id).join(',')}`,
  );
}

main().catch((err) => {
  console.error('[055-seed] FAILED', err);
  process.exit(1);
});
