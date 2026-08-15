/**
 * Spec 054 fail-closed E2E harness — temp DuckDB outside data/warehouse.
 */
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '../../../../');
const CANONICAL_DB = path.join(REPO_ROOT, 'data', 'warehouse', 'voxmetrik.duckdb');
const TEMP_ROOT = path.join(process.env.TEMP || process.env.TMPDIR || '/tmp', 'voxmetrik-054-e2e');
const TEMP_DB = path.join(TEMP_ROOT, 'voxmetrik.duckdb');
const API_HOST = '127.0.0.1';
/** Isolated API — avoid :8000 and Spec 051–053 ports. */
const API_PORT = Number(process.env.E2E_054_API_PORT || 8013);
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
  if (!resolvedTemp.toLowerCase().includes('voxmetrik-054-e2e')) {
    throw new Error(`FAIL-CLOSED: TEMP_DB must live under voxmetrik-054-e2e: ${resolvedTemp}`);
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
  console.log(`[054-harness] canonical(source)=${resolvedCanon}`);
  console.log(`[054-harness] temp(db)=${resolvedTemp}`);
  console.log(`[054-harness] api=${API_BASE}`);
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
      process.env.E2E_054_CORS_ORIGINS ||
      'http://localhost:4203,http://127.0.0.1:4203',
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

async function assertSpec054Surface() {
  const res = await fetch(OPENAPI);
  if (!res.ok) throw new Error(`openapi ${res.status}`);
  const body = await res.json();
  const paths = Object.keys(body.paths || {});
  if (!paths.includes('/api/v1/health')) {
    throw new Error('FAIL-CLOSED: OpenAPI missing /api/v1/health');
  }
  console.log('[054-harness] OpenAPI health OK');
}

export {
  API_BASE,
  API_PORT,
  CANONICAL_DB,
  HEALTH,
  REPO_ROOT,
  TEMP_DB,
  TEMP_ROOT,
  assertSpec054Surface,
  assertTempDbSafe,
  copyCanonicalToTemp,
  startApi,
  waitForOk,
};

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  copyCanonicalToTemp();
  console.log('TEMP_DB=' + TEMP_DB);
}
