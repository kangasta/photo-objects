import { test, expect } from '@playwright/test';

test('login', async ({ page }) => {
  await page.goto('/');

  await page.getByText('Login').click();
  await page.getByLabel('Username').fill(process.env.USERNAME);
  await page.getByLabel('Password').fill(process.env.PASSWORD);
  await page.locator('form').getByText('Login').click();

  await expect(page.getByText('New album')).toBeVisible();
});
