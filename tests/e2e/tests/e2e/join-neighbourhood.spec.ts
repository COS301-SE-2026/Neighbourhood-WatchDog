import {
  test,
  expect,
  FREE_PROPERTY_ID,
  FREE_USER_ID,
  MEMBER_PROPERTY_ID,
  MEMBER_USER_ID,
  PENDING_PROPERTY_ID,
  PENDING_USER_ID,
} from "./fixtures";

const NEIGHBOURHOOD_JOIN_CODE = "E2E_TEST_CODE_001";

test.describe("Join a neighbourhood", () => {
  test("valid join code submits a request", async ({ page }) => {
    await page.setExtraHTTPHeaders({ "X-Mock-User-Id": FREE_USER_ID });
    await page.goto(
      `/dashboard/properties/${FREE_PROPERTY_ID}/neighbourhood/join`,
    );

    await page.locator("#join-code").fill(NEIGHBOURHOOD_JOIN_CODE);
    await page.getByRole("button", { name: /request to join/i }).click();

    await expect(
      page.getByRole("heading", { name: "Awaiting review" }),
    ).toBeVisible();
    await expect(page.getByText("Request submitted")).toBeVisible();
  });

  test("invalid join code shows an inline error", async ({ page }) => {
    await page.setExtraHTTPHeaders({ "X-Mock-User-Id": PENDING_USER_ID });
    await page.goto(
      `/dashboard/properties/${PENDING_PROPERTY_ID}/neighbourhood/join`,
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
    await page.setExtraHTTPHeaders({ "X-Mock-User-Id": PENDING_USER_ID });
    await page.goto(
      `/dashboard/properties/${PENDING_PROPERTY_ID}/neighbourhood/join`,
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
    await page.setExtraHTTPHeaders({ "X-Mock-User-Id": PENDING_USER_ID });
    await page.goto(
      `/dashboard/properties/${MEMBER_PROPERTY_ID}/neighbourhood/join`,
    );

    await page.locator("#join-code").fill(NEIGHBOURHOOD_JOIN_CODE);
    await page.getByRole("button", { name: /request to join/i }).click();

    await expect(page.locator("#join-code-error")).toContainText(
      /already a member/i,
    );
  });
});
