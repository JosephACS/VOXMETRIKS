import { chromium, type FullConfig } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { loginAdmin, loginDemo } from './fixtures/auth';
import { ADMIN_AUTH_FILE, API_URL, AUTH_DIR, BASE_URL, DEMO_AUTH_FILE } from './fixtures/paths';

async function waitForOk(url: string, label: string, timeoutMs = 120_000): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  let lastError = '';
  while (Date.now() < deadline) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(5_000) });
      if (res.ok) return;
      lastError = `${label} responded ${res.status}`;
    } catch (err) {
      lastError = err instanceof Error ? err.message : String(err);
    }
    await new Promise((r) => setTimeout(r, 1_500));
  }
  throw new Error(`Timed out waiting for ${label} at ${url}: ${lastError}`);
}

async function saveAuthState(
  filePath: string,
  loginFn: (page: import('@playwright/test').Page) => Promise<void>,
): Promise<void> {
  const browser = await chromium.launch();
  const context = await browser.newContext({ baseURL: BASE_URL });
  const page = await context.newPage();
  try {
    await loginFn(page);
    await page.getByTestId('app-shell').waitFor({ state: 'visible', timeout: 30_000 });
    await context.storageState({ path: filePath });
  } finally {
    await browser.close();
  }
  if (!fs.existsSync(filePath)) {
    throw new Error(`Storage state was not written: ${filePath}`);
  }
}

async function globalSetup(_config: FullConfig) {
  fs.mkdirSync(AUTH_DIR, { recursive: true });

  await waitForOk(`${API_URL}/api/v1/health`, 'backend API');
  await waitForOk(BASE_URL, 'frontend');

  await saveAuthState(DEMO_AUTH_FILE, loginDemo);
  await saveAuthState(ADMIN_AUTH_FILE, loginAdmin);

  console.log(`[e2e setup] demo auth → ${DEMO_AUTH_FILE}`);
  console.log(`[e2e setup] admin auth → ${ADMIN_AUTH_FILE}`);
}

export default globalSetup;
