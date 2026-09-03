import { test, expect } from "@playwright/test";

const NEIGHBOURHOOD_ID = "10000000-0000-0000-0000-000000000001";

const ADMIN_USER_ID = "20000000-0000-0000-0000-000000000001";

const OFFICER_USER_ID = "20000000-0000-0000-0000-000000000003";

function mockAuthHeaders(userId: string) {
  return {
    Authorization: "Bearer mocktake",
    "X-Mock-User-Id": userId,
  };
}

test.describe("Neighbourhood members", () => {
  test.describe.configure({ mode: "serial" });

  test("admin sees the members and their roles", async ({ page }) => {
    await page.setExtraHTTPHeaders(mockAuthHeaders(ADMIN_USER_ID));
    await page.goto(
      "/dashboard/properies/${NEIGHBOURHOOD_ID}/neighbourhood/members",
    );

    await expect(page.getByLabel("Role for test user")).toHaveValue(
      "NEIGHBOURHOOD_ADMIN",
    );

    await expect(page.getByLabel("Role for E2E officer")).toHaveValue(
      "SECURITY_OFFICER",
    );
  });

  test("non-admin cannot see the members page", async ({ page }) => {
    await page.setExtraHTTPHeaders(mockAuthHeaders(OFFICER_USER_ID));
    await page.goto(
      "/dashboard/properies/${NEIGHBOURHOOD_ID}/neighbourhood/members",
    );

    await expect(
      page.getByText("You do not have admin access to this neighbourhood."),
    ).toBeVisible();
  });

  test("admin changes another member's role", async ({ page }) => {
    await page.setExtraHTTPHeaders(mockAuthHeaders(ADMIN_USER_ID));
    await page.goto(
      "/dashboard/properies/${NEIGHBOURHOOD_ID}/neighbourhood/members",
    );

    const roleSelect = page.getByLabel("Role for E2E Officer");
    await expect(roleSelect).toHaveValue("SECURITY_OFFICER");

    await roleSelect.selectOption("RESIDENT");

    await expect(roleSelect).toHaveValue("RESIDENT");
    await expect(page.getByRole("alert")).toHaveCount(0);
  });

  //last remaining admin cannot demote themselves without handing admin rights to someone else
  test("the only admin cannot remove their own admin role", async ({
    page,
  }) => {
    await page.setExtraHTTPHeaders(mockAuthHeaders(ADMIN_USER_ID));
    await page.goto(
      "/dashboard/properies/${NEIGHBOURHOOD_ID}/neighbourhood/members",
    );

    const roleSelect = page.getByLabel("Role for test User");
    await expect(roleSelect).toHaveValue("RESIDENT");

    await expect(page.getByRole("alert")).toContainText(
      /transfer admin rights/i,
    );
    await expect(roleSelect).toHaveValue("NEIGHBOURHOOD_ADMIN");
  });
});
