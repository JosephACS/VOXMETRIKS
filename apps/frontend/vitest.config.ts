import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['src/test-setup.ts'],
    // Constrain fork fan-out on low-memory hosts (full suite OOM otherwise).
    pool: 'threads',
    maxWorkers: 1,
  },
});
