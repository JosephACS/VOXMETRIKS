import { defineConfig, devices } from '@playwright/test';
import { BASE_URL, DEMO_AUTH_FILE } from '../e2e/fixtures/paths';

/** External servers required by default. Set PLAYWRIGHT_USE_WEBSERVER=1 to auto-start. */
const useManagedServers = process.env.PLAYWRIGHT_USE_WEBSERVER === '1';

export default defineConfig({
  testDir: '../e2e/tests',
  globalSetup: '../e2e/global-setup.ts',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [['list'], ['html', { open: 'never', outputFolder: '../../archive/generated/playwright-report' }]],
  timeout: 90_000,
  expect: { timeout: 20_000 },
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    outputDir: '../../archive/generated/test-results',
    actionTimeout: 20_000,
  },
  projects: [
    {
      name: 'auth',
      testMatch: 'auth.spec.ts',
      use: {
        ...devices['Desktop Chrome'],
        storageState: { cookies: [], origins: [] },
      },
    },
    {
      name: 'authenticated',
      testMatch: /.*\.spec\.ts$/,
      testIgnore: '**/auth.spec.ts',
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
          cwd: '../../apps/backend',
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
          cwd: '../../apps/frontend',
          url: 'http://127.0.0.1:4200',
          reuseExistingServer: true,
          timeout: 180_000,
        },
      ]
    : undefined,
});
