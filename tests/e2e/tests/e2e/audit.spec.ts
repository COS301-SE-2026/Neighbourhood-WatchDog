import { test, expect } from "./fixtures";

test.describe("Audit logs", () => {
  test("list audit records and opens details", async ({ page }) => {
    await page.goto("/dashboard/admin/audit");

    await expect(
      page.getByRole("heading", { name: "Neighbourhood audit logs" }),
    ).toBeVisible();

    await expect(
      page.getByText("CREATE", { exact: true }).first(),
    ).toBeVisible();

    await page.getByRole("button", { name: "View More" }).first().click();
    await expect(page.getByRole("dialog")).toContainText("Record details");
  });
});
