import { test, expect } from "@playwright/test";

test("submit join request shows pending state", async ({ page }) => {
  await page.goto("/joinNeighbourhood");

  await page.waitForSelector("#join-code", { timeout: 10000 });

  const joinCode = page.locator("#join-code");
  await joinCode.fill("NORTH-5F3A");

  const submit = page.getByRole("button", { name: /request to join/i });
  await submit.click({ force: true });

  await expect(
    page.getByText("Request sent — awaiting approval"),
  ).toBeVisible();
});
