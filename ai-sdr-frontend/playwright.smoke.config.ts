import { defineConfig, devices } from '@playwright/test'

/** Dedicated port so E2E does not collide with other Vite apps on 5173. */
const E2E_PORT = process.env.PLAYWRIGHT_PORT ?? '5180'
const E2E_BASE = process.env.PLAYWRIGHT_BASE_URL ?? `http://localhost:${E2E_PORT}`

/** Static smoke — no backend required (login page only). */
export default defineConfig({
  testDir: './e2e',
  testMatch: 'smoke.spec.ts',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: E2E_BASE,
    trace: 'on-first-retry',
  },
  timeout: 30_000,
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: `npm run dev -- --port ${E2E_PORT} --strictPort`,
    url: E2E_BASE,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
})
