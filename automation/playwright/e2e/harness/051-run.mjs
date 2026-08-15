/**
 * Orchestrate Spec 051 isolated E2E: temp DB → API:8010 → seed → Playwright → teardown.
 */
import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  API_BASE,
  API_PORT,
  CANONICAL_DB,
  HEALTH,
  REPO_ROOT,
  TEMP_DB,
  assertSpec051Routes,
  assertTempDbSafe,
  copyCanonicalToTemp,
  startApi,
  waitForOk,
} from './051-isolated-db.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PLAYWRIGHT_DIR = path.resolve(__dirname, '../..');

function runNode(script, env = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [script], {
      cwd: path.dirname(script),
      env: { ...process.env, ...env },
      stdio: 'inherit',
    });
    child.on('exit', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`${script} exited ${code}`));
    });
  });
}

function runPlaywright(dbPath) {
  return new Promise((resolve, reject) => {
    const child = spawn(
      process.platform === 'win32' ? 'npx.cmd' : 'npx',
      ['playwright', 'test', '--config=playwright.051.config.ts'],
      {
        cwd: PLAYWRIGHT_DIR,
        env: {
          ...process.env,
          E2E_API_URL: `${API_BASE}/api/v1`,
          E2E_051_API_PORT: String(API_PORT),
          DB_PATH: dbPath,
          PLAYWRIGHT_BASE_URL: process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:4200',
        },
        stdio: 'inherit',
        shell: process.platform === 'win32',
      },
    );
    child.on('exit', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`playwright exited ${code}`));
    });
  });
}

async function ensureFrontend() {
  const base = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:4200';
  try {
    const res = await fetch(base, { signal: AbortSignal.timeout(3_000) });
    if (res.ok || res.status === 200) {
      console.log(`[051-run] frontend already up at ${base}`);
      return null;
    }
  } catch {
    /* start */
  }
  console.log('[051-run] starting frontend on 4200…');
  const child = spawn(
    process.platform === 'win32' ? 'npm.cmd' : 'npm',
    ['start', '--', '--host', '127.0.0.1', '--port', '4200'],
    {
      cwd: path.join(REPO_ROOT, 'apps', 'frontend'),
      stdio: 'ignore',
      shell: process.platform === 'win32',
      detached: true,
    },
  );
  child.unref();
  await waitForOk(base, 'frontend', 180_000);
  return child;
}

async function main() {
  if (path.resolve(process.env.DB_PATH || '') === path.resolve(CANONICAL_DB)) {
    throw new Error('FAIL-CLOSED: ambient DB_PATH points at canonical warehouse');
  }

  // Ensure a previous run is not still holding the temp DB / port.
  try {
    const res = await fetch(HEALTH, { signal: AbortSignal.timeout(1_500) });
    if (res.ok) {
      throw new Error(
        `FAIL-CLOSED: something is already serving ${HEALTH}. Stop it before e2e:051.`,
      );
    }
  } catch (err) {
    if (err instanceof Error && err.message.includes('FAIL-CLOSED')) throw err;
    // connection refused → free
  }

  const dbPath = copyCanonicalToTemp();
  assertTempDbSafe(dbPath);

  const api = startApi(dbPath);
  let frontendProc = null;
  let exitCode = 0;
  try {
    await waitForOk(HEALTH, 'api-8010');
    await assertSpec051Routes();
    if (path.resolve(dbPath) === path.resolve(CANONICAL_DB)) {
      throw new Error('FAIL-CLOSED: running against canonical DB');
    }
    console.log(`[051-run] API healthy on ${API_BASE} DB_PATH=${dbPath}`);

    process.env.DB_PATH = dbPath;
    process.env.E2E_API_URL = `${API_BASE}/api/v1`;
    if (!String(process.env.DB_PATH).includes('voxmetrik-051-e2e')) {
      throw new Error('FAIL-CLOSED: post-boot DB_PATH is not the isolated temp database');
    }

    await runNode(path.join(__dirname, '051-seed-personas.mjs'), {
      E2E_API_URL: `${API_BASE}/api/v1`,
      E2E_051_API_PORT: String(API_PORT),
      DB_PATH: dbPath,
    });
    frontendProc = await ensureFrontend();
    await runPlaywright(dbPath);
    console.log('[051-run] Playwright OK');
  } catch (err) {
    console.error('[051-run] FAILED', err);
    exitCode = 1;
  } finally {
    try {
      api.kill('SIGTERM');
    } catch {
      /* ignore */
    }
    if (frontendProc && frontendProc.pid) {
      try {
        process.kill(-frontendProc.pid);
      } catch {
        try {
          frontendProc.kill();
        } catch {
          /* ignore */
        }
      }
    }
  }
  process.exit(exitCode);
}

main();
