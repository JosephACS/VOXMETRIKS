/**
 * Spec 055 fail-closed E2E harness — temp DuckDB outside data/warehouse.
 */
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '../../../../');
const CANONICAL_DB = path.join(REPO_ROOT, 'data', 'warehouse', 'voxmetrik.duckdb');
const TEMP_ROOT = path.join(process.env.TEMP || process.env.TMPDIR || '/tmp', 'voxmetrik-055-e2e');
const TEMP_DB = path.join(TEMP_ROOT, 'voxmetrik.duckdb');
const API_HOST = '127.0.0.1';
/** Isolated API — avoid :8000 and Spec 051–054 ports. */
const API_PORT = Number(process.env.E2E_055_API_PORT || 8014);
const API_BASE = `http://${API_HOST}:${API_PORT}`;
const HEALTH = `${API_BASE}/api/v1/health`;
const OPENAPI = `${API_BASE}/openapi.json`;
const OVERVIEW_PATH = '/api/v1/platform-ops/overview';

function assertTempDbSafe(dbPath = TEMP_DB) {
  const resolvedTemp = path.resolve(dbPath);
  const resolvedCanon = path.resolve(CANONICAL_DB);
  const warehouseDir = path.resolve(path.join(REPO_ROOT, 'data', 'warehouse'));
  if (resolvedTemp === resolvedCanon) {
    throw new Error(`FAIL-CLOSED: TEMP_DB equals canonical: ${resolvedTemp}`);
  }
  if (resolvedTemp.toLowerCase().startsWith(warehouseDir.toLowerCase() + path.sep)) {
    throw new Error(`FAIL-CLOSED: TEMP_DB is under data/warehouse: ${resolvedTemp}`);
  }
  if (!resolvedTemp.toLowerCase().includes('voxmetrik-055-e2e')) {
    throw new Error(`FAIL-CLOSED: TEMP_DB must live under voxmetrik-055-e2e: ${resolvedTemp}`);
  }
  return { resolvedTemp, resolvedCanon };
}

function copyCanonicalToTemp() {
  fs.mkdirSync(TEMP_ROOT, { recursive: true });
  if (!fs.existsSync(CANONICAL_DB)) {
    throw new Error(`Canonical DB missing (read-only source): ${CANONICAL_DB}`);
  }
  for (const p of [TEMP_DB, `${TEMP_DB}.wal`]) {
    try {
      if (fs.existsSync(p)) fs.rmSync(p, { force: true });
    } catch (err) {
      throw new Error(
        `FAIL-CLOSED: cannot replace temp DB (is API:${API_PORT} still running?): ${err}`,
      );
    }
  }
  try {
    fs.copyFileSync(CANONICAL_DB, TEMP_DB);
  } catch (err) {
    throw new Error(
      `FAIL-CLOSED: cannot copy canonical → temp (canonical may be locked by another process): ${err}`,
    );
  }
  const wal = `${CANONICAL_DB}.wal`;
  if (fs.existsSync(wal)) {
    try {
      fs.copyFileSync(wal, `${TEMP_DB}.wal`);
    } catch {
      /* WAL may be locked; temp copy still boots from the main file. */
    }
  }
  const { resolvedTemp, resolvedCanon } = assertTempDbSafe();
  console.log(`[055-harness] canonical(source)=${resolvedCanon}`);
  console.log(`[055-harness] temp(db)=${resolvedTemp}`);
  console.log(`[055-harness] api=${API_BASE}`);
  return resolvedTemp;
}

async function waitForOk(url, label, timeoutMs = 120_000) {
  const deadline = Date.now() + timeoutMs;
  let last = '';
  while (Date.now() < deadline) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(5_000) });
      if (res.ok) return;
      last = `${label} status ${res.status}`;
    } catch (err) {
      last = err instanceof Error ? err.message : String(err);
    }
    await new Promise((r) => setTimeout(r, 1_000));
  }
  throw new Error(`Timed out waiting for ${label}: ${last}`);
}

function startApi(dbPath) {
  const env = {
    ...process.env,
    DB_PATH: dbPath,
    GLOBAL_RATE_LIMIT: '0',
    AUTH_RATE_LIMIT: '0',
    CORS_ORIGINS:
      process.env.E2E_055_CORS_ORIGINS ||
      'http://localhost:4204,http://127.0.0.1:4204',
    E2E: '1',
    ORGANIZATION_INVITATION_DELIVERY_MODE: 'local_once',
  };
  const check = path.resolve(env.DB_PATH);
  const canon = path.resolve(CANONICAL_DB);
  if (check === canon) {
    throw new Error('FAIL-CLOSED: refusing to start API with canonical DB_PATH');
  }
  assertTempDbSafe(dbPath);
  const cwd = path.join(REPO_ROOT, 'apps', 'backend');
  const repositoryPython = path.join(
    REPO_ROOT,
    '.venv',
    process.platform === 'win32' ? 'Scripts' : 'bin',
    process.platform === 'win32' ? 'python.exe' : 'python',
  );
  const python =
    process.env.E2E_PYTHON ||
    (fs.existsSync(repositoryPython)
      ? repositoryPython
      : process.platform === 'win32'
        ? 'python.exe'
        : 'python3');
  const child = spawn(
    python,
    ['-m', 'uvicorn', 'app.main:app', '--host', API_HOST, '--port', String(API_PORT)],
    { cwd, env, stdio: ['ignore', 'pipe', 'pipe'] },
  );
  child.stdout.on('data', (buf) => process.stdout.write(`[api${API_PORT}] ${buf}`));
  child.stderr.on('data', (buf) => process.stderr.write(`[api${API_PORT}] ${buf}`));
  return child;
}

async function assertSpec055Surface() {
  const res = await fetch(OPENAPI);
  if (!res.ok) throw new Error(`openapi ${res.status}`);
  const body = await res.json();
  const paths = Object.keys(body.paths || {});
  if (!paths.includes('/api/v1/health')) {
    throw new Error('FAIL-CLOSED: OpenAPI missing /api/v1/health');
  }
  if (paths.includes(OVERVIEW_PATH)) {
    console.log('[055-harness] OpenAPI includes GET /api/v1/platform-ops/overview');
    return;
  }
  const probe = await fetch(`${API_BASE}${OVERVIEW_PATH}`, {
    signal: AbortSignal.timeout(10_000),
  });
  if (probe.status === 404) {
    throw new Error(
      'FAIL-CLOSED: GET /api/v1/platform-ops/overview missing from OpenAPI and returns 404',
    );
  }
  if (probe.status !== 401 && probe.status !== 403) {
    throw new Error(
      `FAIL-CLOSED: overview probe expected 401/403 without auth, got ${probe.status}`,
    );
  }
  console.log(`[055-harness] overview surface OK via unauth probe (${probe.status})`);
}

export {
  API_BASE,
  API_PORT,
  CANONICAL_DB,
  HEALTH,
  OVERVIEW_PATH,
  REPO_ROOT,
  TEMP_DB,
  TEMP_ROOT,
  assertSpec055Surface,
  assertTempDbSafe,
  copyCanonicalToTemp,
  startApi,
  waitForOk,
};

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  copyCanonicalToTemp();
  console.log('TEMP_DB=' + TEMP_DB);
}
