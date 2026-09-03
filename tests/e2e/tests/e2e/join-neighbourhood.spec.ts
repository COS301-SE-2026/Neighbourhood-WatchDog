import { test, expect } from "@playwright/test";

const NEIGHBOURHOOD_JOIN_CODE = "E2E_TEST_CODE_001";

const MEMBER_PROPERTY_ID = "30000000-0000-0000-0000-000000000001";
const MEMBER_USER_ID = "20000000-0000-0000-0000-000000000001";

const PENDING_PROPERTY_ID = "30000000-0000-0000-0000-000000000002";
const PENDING_USER_ID = "20000000-0000-0000-0000-000000000002";

const FREE_PROPERTY_ID = "30000000-0000-0000-0000-000000000003";
const FREE_USER_ID = "20000000-0000-0000-0000-000000000003";

function mockAuthHeaders(userId: string) {
  return {
    Authorization: "Bearer mocktake",
    "X-Mock-User-Id": userId,
  };
}

test.describe("Join a neighbourhood", () => {
  test("valid join code submits a request", async ({ page }) => {
    await page.setExtraHTTPHeaders(mockAuthHeaders(FREE_USER_ID));
    await page.goto(
      "/dashboard/properies/${FREE_PROPERTY_ID/neighbourhood/join",
    );

    await page.locator("#join-code").fill(NEIGHBOURHOOD_JOIN_CODE);
    await page.getByRole("button", { name: /request to join/i }).click();

    await expect(
      page.getByRole("heading", { name: "Awaiting review" }),
    ).toBeVisible();
    await expect(page.getByText("Request submitted")).toBeVisible();
  });

  test("invalid join code shows an inline error", async ({ page }) => {
    await page.setExtraHTTPHeaders(mockAuthHeaders(PENDING_USER_ID));
    await page.goto(
      "/dashboard/properies/${PENDING_PROPERTY_ID/neighbourhood/join",
    );

    await page.locator("#join-code").fill("NOT-A-REAL-CODE");
    await page.getByRole("button", { name: /request to join/i }).click();

    await expect(page.locator("#join-code-error")).toContainText(
      /invalid join code/i,
    );
  });

  test("a property with a pending request cannot submit another", async ({
    page,
  }) => {
    await page.setExtraHTTPHeaders(mockAuthHeaders(PENDING_USER_ID));
    await page.goto(
      "/dashboard/properies/${PENDING_PROPERTY_ID/neighbourhood/join",
    );

    await page.locator("#join-code").fill(NEIGHBOURHOOD_JOIN_CODE);
    await page.getByRole("button", { name: /request to join/i }).click();

    await expect(page.locator("#join-code-error")).toContainText(
      /already have a pending request/i,
    );
  });

  test("a property in the neighbourhood cannot request to join", async ({
    page,
  }) => {
    await page.setExtraHTTPHeaders(mockAuthHeaders(MEMBER_USER_ID));
    await page.goto(
      "/dashboard/properies/${MEMBER_PROPERTY_ID/neighbourhood/join",
    );

    await page.locator("#join-code").fill(NEIGHBOURHOOD_JOIN_CODE);
    await page.getByRole("button", { name: /request to join/i }).click();

    await expect(page.locator("#join-code-error")).toContainText(
      /already a member/i,
    );
  });
});
