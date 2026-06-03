import { test, expect } from "@playwright/test";

test("approve join request", async ({ page }) => {
  await page.goto("/request-page");

  await page.waitForSelector('[role="article"]', { timeout: 30000 });

  const approve = page.getByRole("button", { name: /approve/i }).first();
  await approve.click();

  await expect(page.getByText(/approved/i).first()).toBeVisible();
});

test("deny join request", async ({ page }) => {
  await page.goto("/request-page");

  await page.waitForSelector('[role="article"]', { timeout: 30000 });

  const deny = page.getByRole("button", { name: /deny/i }).first();
  await deny.click();

  await expect(page.getByText(/denied/i).first()).toBeVisible();
});
