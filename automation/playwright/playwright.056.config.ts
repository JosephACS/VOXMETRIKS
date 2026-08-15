import path from 'node:path';
import { defineConfig, devices } from '@playwright/test';

/**
 * Spec 056 isolated config — no globalSetup against the ambient :8000 demo DB.
 * Expects E2E_API_URL + DB_PATH from e2e/harness/056-run.mjs.
 */
const pkgDir = __dirname;

export default defineConfig({
  testDir: path.join(pkgDir, 'e2e/tests'),
  testMatch: /final-professional-product-closure\.spec\.ts/,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: path.join(pkgDir, 'playwright-report-056') }],
  ],
  outputDir: path.join(pkgDir, 'test-results-056'),
  timeout: 120_000,
  expect: { timeout: 25_000 },
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:4205',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 25_000,
    storageState: { cookies: [], origins: [] },
  },
  projects: [
    {
      name: '056-desktop',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1366, height: 768 },
      },
    },
    {
      name: '056-mobile',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 390, height: 844 },
        isMobile: true,
        hasTouch: true,
      },
    },
  ],
});
