import { test, expect } from '@playwright/test';

/**
 * LIVE simulation: https://curago.pages.dev against production
 * Render backend + production Supabase. Read-only assertions
 * (no approvals, no mutations). Run: npx playwright test e2e/live.spec.ts
 */
const SITE = 'https://curago.pages.dev';

test('live: doctor queue renders real tickets, zero JS errors', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(String(e).slice(0, 150)));
  await page.goto(`${SITE}/doctor`, { waitUntil: 'networkidle', timeout: 60000 });
  const cards = page.locator('.patient-card');
  await expect(cards.first()).toBeVisible({ timeout: 30000 });
  expect(await cards.count()).toBeGreaterThan(0);
  expect(errors).toEqual([]);
});

test('live: analytics tab shows production breakdowns', async ({ page }) => {
  await page.goto(`${SITE}/doctor`, { waitUntil: 'networkidle', timeout: 60000 });
  await page.getByText('📊 Analytics').click();
  await expect(page.getByText('Epidemic Analytics & Outbreaks')).toBeVisible({ timeout: 30000 });
  await expect(page.getByText('Total Patients')).toBeVisible();
  await expect(page.getByText('Daily Ticket Volume')).toBeVisible();
  await expect(page.getByText('Order Fulfillment')).toBeVisible();
});

test('live: adaptive Rx card served by production backend', async ({ page }) => {
  await page.goto(`${SITE}/doctor`, { waitUntil: 'networkidle', timeout: 60000 });
  // recommend card appears once the live /api/recommend call resolves
  await expect(page.getByText('Adaptive Prescription (', { exact: false }).first()).toBeVisible({ timeout: 45000 });
});
