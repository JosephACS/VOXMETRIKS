import path from 'node:path';
import { defineConfig, devices } from '@playwright/test';
import { BASE_URL } from './e2e/fixtures/paths';

/**
 * Spec 051 isolated config — no globalSetup against the ambient :8000 demo DB.
 * Expects E2E_API_URL + DB_PATH from e2e/harness/051-run.mjs.
 */
const pkgDir = __dirname;

export default defineConfig({
  testDir: path.join(pkgDir, 'e2e/tests'),
  testMatch: /artist-professional-journey\.spec\.ts/,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [['list'], ['html', { open: 'never', outputFolder: path.join(pkgDir, 'playwright-report-051') }]],
  timeout: 90_000,
  expect: { timeout: 20_000 },
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    outputDir: path.join(pkgDir, 'test-results-051'),
    actionTimeout: 20_000,
    storageState: { cookies: [], origins: [] },
  },
  projects: [
    {
      name: '051-auth',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
