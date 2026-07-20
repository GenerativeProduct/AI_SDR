import { test, expect } from '@playwright/test'

const ADMIN_EMAIL = process.env.SDR_E2E_EMAIL ?? 'admin@sdr.local'
const ADMIN_PASSWORD = process.env.SDR_E2E_PASSWORD ?? 'admin123'

async function login(page: import('@playwright/test').Page) {
  await page.goto('/login')
  await page.getByLabel('Email').fill(ADMIN_EMAIL)
  await page.getByLabel('Password').fill(ADMIN_PASSWORD)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.getByRole('heading', { name: 'Control the full SDR pipeline' })).toBeVisible({
    timeout: 15_000,
  })
}

test.describe('live auth flow @live', () => {
  test('login reaches dashboard with metrics', async ({ page }) => {
    await login(page)
    await expect(page.getByRole('heading', { name: 'Where work exists right now' })).toBeVisible()
    await expect(page.getByText('System readiness')).toBeVisible()
  })

  test('pipeline page loads', async ({ page }) => {
    await login(page)
    await page.getByRole('link', { name: 'Open pipeline chat' }).click()
    await expect(page.getByText('Natural language ICP → full SDR agent pipeline')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Run Pipeline' })).toBeVisible()
  })

  test('discovery page has run discovery UI', async ({ page }) => {
    await login(page)
    await page.goto('/discovery')
    await expect(page.getByRole('heading', { name: 'Discovery' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Run Discovery' })).toBeVisible()
  })

  test('outreach page has create campaign UI', async ({ page }) => {
    await login(page)
    await page.goto('/outreach')
    await expect(page.getByRole('heading', { name: 'Outreach Inbox' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Create' })).toBeVisible()
  })

  test('meetings page has create request UI', async ({ page }) => {
    await login(page)
    await page.goto('/meetings')
    await expect(page.getByRole('heading', { name: 'Meetings & CRM' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Create request' })).toBeVisible()
  })

  test('settings theme toggle', async ({ page }) => {
    await login(page)
    await page.goto('/settings')
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible()
    await expect(page.getByText('Light (chatbase workspace)')).toBeVisible()
  })
})
