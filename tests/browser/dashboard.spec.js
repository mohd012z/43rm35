const { test, expect } = require('@playwright/test');

for (const viewport of [
  { name: 'desktop', width: 1280, height: 800 },
  { name: 'mobile', width: 390, height: 844 },
]) {
  test(`${viewport.name}: dashboard renders and filters`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text());
    });

    await page.goto('/web/index.html');
    await expect(page.locator('body')).toContainText('43rm35');
    await expect(page.locator('tbody tr').first()).toBeVisible();

    const rowsBefore = await page.locator('tbody tr').count();
    expect(rowsBefore).toBeGreaterThan(0);

    const search = page.locator('input[type="search"], input').first();
    await expect(search).toBeVisible();
    await search.fill('__no_such_channel__');
    await expect(page.locator('tbody tr')).toHaveCount(0);

    expect(errors, `browser console/page errors: ${errors.join(' | ')}`).toEqual([]);
  });
}
