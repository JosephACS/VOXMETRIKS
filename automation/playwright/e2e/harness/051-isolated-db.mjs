/**
 * Spec 051 fail-closed E2E harness — temp DuckDB outside data/warehouse.
 *
 * Usage (orchestrator): node e2e/harness/051-run.mjs
 */
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '../../../../');
const CANONICAL_DB = path.join(REPO_ROOT, 'data', 'warehouse', 'voxmetrik.duckdb');
const TEMP_ROOT = path.join(process.env.TEMP || process.env.TMPDIR || '/tmp', 'voxmetrik-051-e2e');
const TEMP_DB = path.join(TEMP_ROOT, 'voxmetrik.duckdb');
const API_HOST = '127.0.0.1';
/** Isolated API must not collide with a local server on the canonical warehouse. */
const API_PORT = Number(process.env.E2E_051_API_PORT || 8010);
const API_BASE = `http://${API_HOST}:${API_PORT}`;
const HEALTH = `${API_BASE}/api/v1/health`;
const OPENAPI = `${API_BASE}/openapi.json`;

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
  if (!resolvedTemp.toLowerCase().includes('voxmetrik-051-e2e')) {
    throw new Error(`FAIL-CLOSED: TEMP_DB must live under voxmetrik-051-e2e: ${resolvedTemp}`);
  }
  return { resolvedTemp, resolvedCanon };
}

function copyCanonicalToTemp() {
  fs.mkdirSync(TEMP_ROOT, { recursive: true });
  if (!fs.existsSync(CANONICAL_DB)) {
    throw new Error(`Canonical DB missing (read-only source): ${CANONICAL_DB}`);
  }
  // Drop a previous temp DB if a stale API still holds it.
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
      // WAL may be locked; temp copy still boots from the main file.
    }
  }
  const { resolvedTemp, resolvedCanon } = assertTempDbSafe();
  console.log(`[051-harness] canonical(source)=${resolvedCanon}`);
  console.log(`[051-harness] temp(db)=${resolvedTemp}`);
  console.log(`[051-harness] api=${API_BASE}`);
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
    E2E: '1',
  };
  const check = path.resolve(env.DB_PATH);
  const canon = path.resolve(CANONICAL_DB);
  if (check === canon) {
    throw new Error('FAIL-CLOSED: refusing to start API with canonical DB_PATH');
  }
  assertTempDbSafe(dbPath);
  const cwd = path.join(REPO_ROOT, 'apps', 'backend');
  const python =
    process.env.E2E_PYTHON ||
    (process.platform === 'win32' ? 'python' : 'python3');
  const child = spawn(
    python,
    ['-m', 'uvicorn', 'app.main:app', '--host', API_HOST, '--port', String(API_PORT)],
    { cwd, env, stdio: ['ignore', 'pipe', 'pipe'], shell: process.platform === 'win32' },
  );
  child.stdout.on('data', (buf) => process.stdout.write(`[api${API_PORT}] ${buf}`));
  child.stderr.on('data', (buf) => process.stderr.write(`[api${API_PORT}] ${buf}`));
  return child;
}

async function assertSpec051Routes() {
  const res = await fetch(OPENAPI);
  if (!res.ok) throw new Error(`openapi ${res.status}`);
  const body = await res.json();
  const paths = Object.keys(body.paths || {});
  const required = [
    '/api/v1/artist-access/discover',
    '/api/v1/platform/catalog-reviews',
    '/api/v1/platform/artist-requests',
  ];
  for (const p of required) {
    if (!paths.includes(p)) {
      throw new Error(`FAIL-CLOSED: OpenAPI missing ${p}`);
    }
  }
  console.log('[051-harness] OpenAPI Spec 051 routes OK');
}

export {
  API_BASE,
  API_PORT,
  CANONICAL_DB,
  HEALTH,
  REPO_ROOT,
  TEMP_DB,
  TEMP_ROOT,
  assertSpec051Routes,
  assertTempDbSafe,
  copyCanonicalToTemp,
  startApi,
  waitForOk,
};

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  copyCanonicalToTemp();
  console.log('TEMP_DB=' + TEMP_DB);
}
