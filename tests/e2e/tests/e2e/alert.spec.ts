import { test, expect, PROPERTY_ID } from "./fixtures";

test.describe("Alerts", () => {
  test("lists alerts and acknowledges alert", async ({ page }) => {
    await page.goto(`/dashboard/properties/${PROPERTY_ID}/alerts`);

    await expect(
      page.getByRole("heading", { name: "Property alerts" }),
    ).toBeVisible();
    const alertCard = page
      .getByRole("article")
      .filter({ hasText: "Person detected" })
      .first();
    await expect(alertCard).toBeVisible();

    await alertCard.getByRole("button", { name: /acknowledge/i }).click();
    await expect(alertCard).toContainText("Acknowledged");
  });
});
