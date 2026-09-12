import { test } from '@playwright/test'
import { shoot } from '../helpers/screenshot'
import { login, expectPostVisible, expectUserProvisioned } from '../helpers/wordpress'

test.describe('wordpress post-upgrade', () => {
  test('the post seeded before the upgrade is still served', async ({ page }, testInfo) => {
    await expectPostVisible(page)
    await shoot(page, testInfo, 'post-upgrade-post')
  })

  test('ldap login still works after the upgrade', async ({ page }, testInfo) => {
    await login(page)
    await expectUserProvisioned(page)
    await shoot(page, testInfo, 'post-upgrade-users')
  })
})
