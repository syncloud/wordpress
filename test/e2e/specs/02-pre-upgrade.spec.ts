import { test } from '@playwright/test'
import { shoot } from '../helpers/screenshot'
import { login, expectPostVisible } from '../helpers/wordpress'

test.describe('wordpress pre-upgrade', () => {
  test('the store build serves the seeded post and accepts an ldap login', async ({ page }, testInfo) => {
    await login(page)
    await shoot(page, testInfo, 'pre-upgrade-dashboard')
    await expectPostVisible(page)
    await shoot(page, testInfo, 'pre-upgrade-post')
  })
})
