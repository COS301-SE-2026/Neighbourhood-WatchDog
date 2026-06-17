import { test, expect } from "@playwright/test";

test("acknowledge alert flow", async ({ page }) => {
  test.setTimeout(90000);

  await page.goto("/alert");

  await page.waitForSelector('[role="article"]', { timeout: 60000 });

  const ack = page.getByRole("button", { name: /acknowledge/i }).first();
  await ack.click();

  await expect(page.getByText(/acknowledged/i).first()).toBeVisible();
});
