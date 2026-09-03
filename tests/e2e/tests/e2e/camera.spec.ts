import { test, expect, PROPERTY_ID } from "./fixtures";

test.describe("Cameras", () => {
  test("lists cameras", async ({ page }) => {
    await page.goto(`/dashboard/properties/${PROPERTY_ID}/cameras`);

    await expect(
      page.getByRole("heading", { name: "Cameras" }).first(),
    ).toBeVisible();
    await expect(page.getByText("Back Gate", { exact: true })).toBeVisible();
  });

  test("adds a camera to property", async ({ page }) => {
    await page.goto(`/dashboard/properties/${PROPERTY_ID}/cameras`);
    await page
      .getByRole("button", { name: /add camera/i })
      .first()
      .click();

    await page.getByLabel("Camera Name").fill("E2E Camera");
    await page.getByLabel("Camera Location").fill("E2E Gate");
    await page.getByLabel("RSTP URL").fill("rstp://e2e-camera.local:554/e2e");
    await page.getByRole("button", { name: "Acknowledge" }).click();

    await expect(page.getByText("E2E Camera", { exact: true })).toBeVisible();
  });
});
