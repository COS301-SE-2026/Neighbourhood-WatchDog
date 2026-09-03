import { test, expect, PROPERTY_ID } from "./fixtures";

test.describe("Cameras", () => {
  test("lists cameras", async ({ page }) => {
    await page.goto(`dashboard/properties/${PROPERTY_ID}/cameras`);

    await expect(
      page.getByRole("heading", { name: "Cameras" }).first(),
    ).toBeVisible();
    await expect(page.getByText("Back Gate", { exact: true })).toBeVisible();
  });
});
