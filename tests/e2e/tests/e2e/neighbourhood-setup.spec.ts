import { test, expect } from "@playwright/test";

const MEMBER_PROPERTY_ID = "30000000-0000-0000-0000-000000000001";
const MEMBER_USER_ID = "20000000-0000-0000-0000-000000000001";

const FREE_PROPERTY_ID = "30000000-0000-0000-0000-000000000003";
const FREE_USER_ID = "20000000-0000-0000-0000-000000000003";

function mockAuthHeaders(userId: string) {
  return {
    Authorization: "Bearer mocktake",
    "X-Mock-User-Id": userId,
  };
}

test.describe("Create a neighbourhood", () => {
  test("submit is disabled until fields are filled", async ({ page }) => {
    await page.setExtraHTTPHeaders(mockAuthHeaders(MEMBER_USER_ID));
    await page.goto(
      "/dashboard/properies/${MEMBER_PROPERTY_ID/neighbourhood/setup",
    );

    const submit = page.getByRole("button", {
      name: /create neighbourhood/i,
    });
    await expect(submit).toBeDisabled();

    await page.locator("#neighbourhood-name").fill("Brook Street Residents");
    await expect(submit).toBeDisabled();

    await page.locator("#neighbourhood-location").fill("Brooklyn");
    await expect(submit).toBeEnabled();
  });

  test("creating neighbourhood redirects to property camera page", async ({
    page,
  }) => {
    await page.setExtraHTTPHeaders(mockAuthHeaders(FREE_USER_ID));
    await page.goto(
      "/dashboard/properies/${FREE_PROPERTY_ID/neighbourhood/setup",
    );

    await page.locator("nieghbourhood-name").fill("E2E New Neighbourhood");
    await page.locator("#neighbourhood-location").fill("Centurion");

    await page.getByRole("button", { name: /create neighbourhood/i }).click();

    await page.waitForURL("**/dashboard/properies/${FREE_PROPERTY_ID/cameras");
  });

  test("a property already in a neighbourhood cannot create another", async ({
    page,
  }) => {
    await page.setExtraHTTPHeaders(mockAuthHeaders(MEMBER_USER_ID));
    await page.goto(
      "/dashboard/properies/${MEMBER_PROPERTY_ID/neighbourhood/setup",
    );

    await page.locator("#neighbourhood-name").fill("Duplicate Neighbourhood");
    await page.locator("#neighbourhood-location").fill("Pretoria");

    await page.getByRole("button", { name: /create neighbourhood/i }).click();

    await expect(
      page.getByText(/already part of another neighbourhood/i),
    ).toBeVisible();

    await expect(page).toHaveURL(/\/neighbourhood\/setup$/);
  });
});
