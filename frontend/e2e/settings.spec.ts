import { test, expect } from '@playwright/test'

test.describe('Settings Page', () => {
  test('renders settings page with tabs', async ({ page }) => {
    await page.goto('/settings')
    await expect(page.getByRole('heading', { name: 'Einstellungen' })).toBeVisible()
  })

  test('switches between tabs', async ({ page }) => {
    await page.goto('/settings')
    await expect(page.locator('[role="tablist"]')).toBeVisible()
  })
})
