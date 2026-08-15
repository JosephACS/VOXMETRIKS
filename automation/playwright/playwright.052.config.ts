import path from 'node:path';
import { defineConfig, devices } from '@playwright/test';

/**
 * Spec 052 isolated config — no globalSetup against the ambient :8000 demo DB.
 * Expects E2E_API_URL + DB_PATH from e2e/harness/052-run.mjs.
 */
const pkgDir = __dirname;

export default defineConfig({
  testDir: path.join(pkgDir, 'e2e/tests'),
  testMatch: /professional-checkout-journey\.spec\.ts/,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: path.join(pkgDir, 'playwright-report-052') }],
  ],
  outputDir: path.join(pkgDir, 'test-results-052'),
  timeout: 90_000,
  expect: { timeout: 20_000 },
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:4201',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 20_000,
    storageState: { cookies: [], origins: [] },
  },
  projects: [
    {
      name: '052-desktop',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1366, height: 768 },
      },
    },
    {
      name: '052-mobile',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 390, height: 844 },
        isMobile: true,
        hasTouch: true,
      },
    },
  ],
});
