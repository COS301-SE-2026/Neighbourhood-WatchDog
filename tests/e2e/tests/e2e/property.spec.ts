import { test, expect, PROPERTY_ID } from "./fixtures";

test.describe("Properties", () => {
  test("shows the selected property camera workspace", async ({ page }) => {
    await page.goto(`/dashboard/properties/${PROPERTY_ID}/cameras`);

    await expect(
      page.getByText("123 Test Street", { exact: false }),
    ).toBeVisible();

    await expect(
      page.getByRole("heading", { name: "Cameras" }).first(),
    ).toBeVisible();
  });
});
