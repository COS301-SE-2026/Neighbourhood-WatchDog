import { test, expect } from "@playwright/test";

test.use({ storageState: { cookies: [], origins: [] } });

test("logged-out visitor can open Help from the landing page", async ({ page }) => {
  await page.goto("http://localhost:3000/");

  await page.getByRole("link", { name: "Help", exact: true }).first().click();

  await expect(page).toHaveURL(/\/help$/);
  await expect(page.getByRole("heading", { name: "Help centre" })).toBeVisible();
});

test("logged-out visitor can open Help from the mobile menu", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("http://localhost:3000/");

  await page.getByRole("button", { name: "Open menu" }).click();
  await page.getByRole("link", { name: "Help", exact: true }).last().click();

  await expect(page).toHaveURL(/\/help$/);
  await expect(page.getByRole("heading", { name: "Help centre" })).toBeVisible();
});
