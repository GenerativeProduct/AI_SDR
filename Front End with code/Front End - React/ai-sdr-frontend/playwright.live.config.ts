import { defineConfig, devices } from '@playwright/test'

const E2E_PORT = process.env.PLAYWRIGHT_PORT ?? '5180'
const E2E_BASE = process.env.PLAYWRIGHT_BASE_URL ?? `http://localhost:${E2E_PORT}`

/**
 * Live integration — requires AI SDR backend on :8011 with SDR_AUTH_ENABLED=true.
 * Frontend dev server proxies /api → backend.
 */
export default defineConfig({
  testDir: './e2e',
  testMatch: 'live.spec.ts',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: E2E_BASE,
    trace: 'on-first-retry',
  },
  timeout: 60_000,
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command:
        'cd .. && SDR_AUTH_ENABLED=true SDR_CORS_ORIGINS=http://localhost:5180 python3 -m uvicorn ai_sdr_platform.src.api.app:app --port 8011',
      url: 'http://127.0.0.1:8011/health',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: `npm run dev -- --port ${E2E_PORT} --strictPort`,
      url: E2E_BASE,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
})
