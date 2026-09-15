import { Page, expect } from '@playwright/test'

const user = process.env.PLAYWRIGHT_DEVICE_USER ?? 'user'
const password = process.env.PLAYWRIGHT_DEVICE_PASSWORD ?? 'Password1'

export const postTitle = 'syncloud title'
export const postBody = 'syncloud paragraph'

async function dump(page: Page, label: string) {
  console.log(`[${label}] url=${page.url()}`)
  console.log(`[${label}] title=${await page.title().catch(() => '?')}`)
  const html = await page.content().catch(() => '')
  console.log(`[${label}] html=\n${html.slice(0, 4000)}`)
}

function adminBar(page: Page) {
  return page.locator('#wpadminbar').or(page.locator('#dashboard-widgets'))
}

export async function login(page: Page) {
  await page.goto('/wp-admin/')

  const autheliaUser = page.locator('#username-textfield')
  const wpUser = page.locator('#user_login')

  try {
    await expect(autheliaUser.or(wpUser).or(adminBar(page)).first()).toBeVisible({ timeout: 60_000 })
  } catch (e) {
    await dump(page, 'no-login-form-and-no-dashboard')
    throw e
  }

  if (await autheliaUser.isVisible()) {
    await autheliaUser.fill(user)
    await page.locator('#password-textfield').fill(password)
    await page.locator('#sign-in-button').click()
  } else if (await wpUser.isVisible()) {
    await wpUser.fill(user)
    await page.locator('#user_pass').fill(password)
    await page.locator('#wp-submit').click()
  }
  await expectAtDashboard(page)
}

export async function expectAtDashboard(page: Page) {
  try {
    await expect(adminBar(page).first()).toBeVisible({ timeout: 60_000 })
  } catch (e) {
    await dump(page, 'dashboard-not-found')
    throw e
  }
}

export async function expectUserProvisioned(page: Page) {
  await page.goto('/wp-admin/users.php')
  try {
    await expect(page.getByText(user, { exact: false }).first()).toBeVisible()
  } catch (e) {
    await dump(page, 'sso-user-missing')
    throw e
  }
}

export async function expectPostVisible(page: Page) {
  await page.goto('/')
  try {
    await expect(page.getByText(postTitle, { exact: false }).first()).toBeVisible()
    await expect(page.getByText(postBody, { exact: false }).first()).toBeVisible()
  } catch (e) {
    await dump(page, 'post-not-visible')
    throw e
  }
}
