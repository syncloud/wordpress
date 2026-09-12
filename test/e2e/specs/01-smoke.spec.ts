import { test } from '@playwright/test'
import { shoot } from '../helpers/screenshot'
import { login, expectUserProvisioned } from '../helpers/wordpress'

test.describe('wordpress smoke', () => {
  test('log in through ldap and reach the dashboard', async ({ page }, testInfo) => {
    await login(page)
    await shoot(page, testInfo, 'dashboard')
  })

  test('the syncloud user is provisioned in wordpress', async ({ page }, testInfo) => {
    await login(page)
    await expectUserProvisioned(page)
    await shoot(page, testInfo, 'users')
  })
})
