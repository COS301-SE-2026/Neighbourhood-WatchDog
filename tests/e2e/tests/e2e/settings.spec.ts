import { test, expect, CREATE_USER_ID } from "./fixtures";

test.describe("Settings", () => {
  test("loads and updates account settings", async ({ page }) => {
    await page.setExtraHTTPHeaders({ "X-Mock-User-Id": CREATE_USER_ID });
    await page.goto("/dashboard/settings");

    await expect(
      page.getByRole("heading", { name: "Account settings" }),
    ).toBeVisible();

    await expect(page.getByLabel("Email")).toHaveValue(
      "e2e.create-neighbourhood@example.com",
    );

    await page.getByLabel("First name").fill("E2E");
    await page.getByLabel("Last name").fill("Settings User");
    await page.getByLabel("Phone number").fill("+27 82 000 0000");
    await page.getByRole("button", { name: "Save changes" }).click();

    await expect(page.getByText("Settings updated")).toBeVisible();
  });
});
