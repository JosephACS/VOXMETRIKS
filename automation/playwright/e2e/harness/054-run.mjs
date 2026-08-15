/**
 * Orchestrate Spec 054 isolated E2E: temp DB → API:8013 → seed → Playwright → teardown.
 */
import { spawn, spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  API_BASE,
  API_PORT,
  CANONICAL_DB,
  HEALTH,
  REPO_ROOT,
  assertSpec054Surface,
  assertTempDbSafe,
  copyCanonicalToTemp,
  startApi,
  waitForOk,
} from './054-isolated-db.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PLAYWRIGHT_DIR = path.resolve(__dirname, '../..');
const FRONTEND_PORT = Number(process.env.E2E_054_FRONTEND_PORT || 4203);
const FRONTEND_BASE = `http://127.0.0.1:${FRONTEND_PORT}`;

function stopOwnedProcessTree(child) {
  if (!child?.pid) return;
  if (process.platform === 'win32') {
    spawnSync('taskkill.exe', ['/PID', String(child.pid), '/T', '/F'], {
      stdio: 'ignore',
    });
    return;
  }
  try {
    child.kill('SIGTERM');
  } catch {
    /* already stopped */
  }
}

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

function runPlaywright(dbPath, extraArgs = []) {
  return new Promise((resolve, reject) => {
    const playwrightCli = path.join(
      PLAYWRIGHT_DIR,
      'node_modules',
      '@playwright',
      'test',
      'cli.js',
    );
    const child = spawn(
      process.execPath,
      [playwrightCli, 'test', '--config=playwright.054.config.ts', ...extraArgs],
      {
        cwd: PLAYWRIGHT_DIR,
        env: {
          ...process.env,
          E2E_API_URL: `${API_BASE}/api/v1`,
          E2E_054_API_PORT: String(API_PORT),
          DB_PATH: dbPath,
          PLAYWRIGHT_BASE_URL: process.env.PLAYWRIGHT_BASE_URL || FRONTEND_BASE,
        },
        stdio: 'inherit',
      },
    );
    child.on('exit', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`playwright exited ${code}`));
    });
  });
}

async function ensureFrontend() {
  const base = process.env.PLAYWRIGHT_BASE_URL || FRONTEND_BASE;
  try {
    const res = await fetch(base, { signal: AbortSignal.timeout(3_000) });
    if (res.ok || res.status === 200) {
      throw new Error(
        `FAIL-CLOSED: ${base} is already serving. Spec 054 must compile the current working tree.`,
      );
    }
  } catch (err) {
    if (err instanceof Error && err.message.includes('FAIL-CLOSED')) throw err;
    /* start */
  }
  console.log(`[054-run] starting isolated frontend on ${FRONTEND_PORT}…`);
  const angularCli = path.join(
    REPO_ROOT,
    'apps',
    'frontend',
    'node_modules',
    '@angular',
    'cli',
    'bin',
    'ng.js',
  );
  const child = spawn(
    process.execPath,
    [angularCli, 'serve', '--host', '127.0.0.1', '--port', String(FRONTEND_PORT)],
    {
      cwd: path.join(REPO_ROOT, 'apps', 'frontend'),
      stdio: ['ignore', 'pipe', 'pipe'],
    },
  );
  child.stdout?.on('data', (buf) => process.stdout.write(`[fe${FRONTEND_PORT}] ${buf}`));
  child.stderr?.on('data', (buf) => process.stderr.write(`[fe${FRONTEND_PORT}] ${buf}`));
  await waitForOk(base, 'frontend', 300_000);
  return child;
}

async function main() {
  if (path.resolve(process.env.DB_PATH || '') === path.resolve(CANONICAL_DB)) {
    throw new Error('FAIL-CLOSED: ambient DB_PATH points at canonical warehouse');
  }

  try {
    const res = await fetch(HEALTH, { signal: AbortSignal.timeout(1_500) });
    if (res.ok) {
      throw new Error(
        `FAIL-CLOSED: something is already serving ${HEALTH}. Stop it before e2e:054.`,
      );
    }
  } catch (err) {
    if (err instanceof Error && err.message.includes('FAIL-CLOSED')) throw err;
  }

  const dbPath = copyCanonicalToTemp();
  assertTempDbSafe(dbPath);

  const api = startApi(dbPath);
  let frontendProc = null;
  let exitCode = 0;
  try {
    await waitForOk(HEALTH, 'api-8013');
    await assertSpec054Surface();
    if (path.resolve(dbPath) === path.resolve(CANONICAL_DB)) {
      throw new Error('FAIL-CLOSED: running against canonical DB');
    }
    console.log(`[054-run] API healthy on ${API_BASE} DB_PATH=${dbPath}`);

    process.env.DB_PATH = dbPath;
    process.env.E2E_API_URL = `${API_BASE}/api/v1`;
    if (!String(process.env.DB_PATH).includes('voxmetrik-054-e2e')) {
      throw new Error('FAIL-CLOSED: post-boot DB_PATH is not the isolated temp database');
    }

    await runNode(path.join(__dirname, '054-seed-personas.mjs'), {
      E2E_API_URL: `${API_BASE}/api/v1`,
      E2E_054_API_PORT: String(API_PORT),
      DB_PATH: dbPath,
    });
    frontendProc = await ensureFrontend();
    await runPlaywright(dbPath, process.argv.slice(2));
    console.log('[054-run] Playwright OK');
  } catch (err) {
    console.error('[054-run] FAILED', err);
    exitCode = 1;
  } finally {
    stopOwnedProcessTree(api);
    stopOwnedProcessTree(frontendProc);
  }
  process.exit(exitCode);
}

main();
