import path from 'node:path';
import { defineConfig, devices } from '@playwright/test';
import { BASE_URL, DEMO_AUTH_FILE } from './e2e/fixtures/paths';

/** External servers required by default. Set PLAYWRIGHT_USE_WEBSERVER=1 to auto-start. */
const useManagedServers = process.env.PLAYWRIGHT_USE_WEBSERVER === '1';

const pkgDir = __dirname;

export default defineConfig({
  testDir: path.join(pkgDir, 'e2e/tests'),
  globalSetup: path.join(pkgDir, 'e2e/global-setup.ts'),
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [['list'], ['html', { open: 'never', outputFolder: path.join(pkgDir, 'playwright-report') }]],
  timeout: 90_000,
  expect: { timeout: 20_000 },
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    outputDir: path.join(pkgDir, 'test-results'),
    actionTimeout: 20_000,
  },
  projects: [
    {
      name: 'auth',
      testMatch: /(auth|identity-first-access|release-candidate-final|final-technical-release)\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        storageState: { cookies: [], origins: [] },
      },
    },
    {
      name: 'authenticated',
      testMatch: /.*\.spec\.ts$/,
      testIgnore: [
        '**/auth.spec.ts',
        '**/identity-first-access.spec.ts',
        '**/release-candidate-final.spec.ts',
        '**/final-technical-release.spec.ts',
      ],
      use: {
        ...devices['Desktop Chrome'],
        storageState: DEMO_AUTH_FILE,
      },
    },
  ],
  webServer: useManagedServers
    ? [
        {
          command: 'uvicorn app.main:app --host 127.0.0.1 --port 8000',
          cwd: path.join(pkgDir, '../../apps/backend'),
          url: 'http://127.0.0.1:8000/api/v1/health',
          reuseExistingServer: true,
          timeout: 120_000,
          env: {
            GLOBAL_RATE_LIMIT: '0',
            AUTH_RATE_LIMIT: '0',
            E2E: '1',
          },
        },
        {
          command: 'npm start -- --host 127.0.0.1 --port 4200',
          cwd: path.join(pkgDir, '../../apps/frontend'),
          url: 'http://127.0.0.1:4200',
          reuseExistingServer: true,
          timeout: 180_000,
        },
      ]
    : undefined,
});
