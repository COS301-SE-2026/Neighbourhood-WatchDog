import {
  test,
  expect,
  CREATE_PROPERTY_ID,
  CREATE_USER_ID,
  MEMBER_PROPERTY_ID,
  MEMBER_USER_ID,
} from "./fixtures";

test.describe("Create a neighbourhood", () => {
  test("submit is disabled until fields are filled", async ({ page }) => {
    await page.setExtraHTTPHeaders({ "X-Mock-User-Id": MEMBER_USER_ID });
    await page.goto(
      `/dashboard/properties/${MEMBER_PROPERTY_ID}/neighbourhood/setup`,
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
    await page.setExtraHTTPHeaders({ "X-Mock-User-Id": CREATE_USER_ID });
    await page.goto(
      `/dashboard/properties/${CREATE_PROPERTY_ID}/neighbourhood/setup`,
    );

    await page.locator("neighbourhood-name").fill("E2E New Neighbourhood");
    await page.locator("#neighbourhood-location").fill("Centurion");

    await page.getByRole("button", { name: /create neighbourhood/i }).click();

    await page.waitForURL(
      "**/dashboard/properties/${CREATE_PROPERTY_ID}/cameras",
    );
    expect(page.url()).toContain(
      `/dashboard/properties/${CREATE_PROPERTY_ID}/cameras`,
    );
    await expect(
      page.getByRole("heading", { name: "Cameras" }).first(),
    ).toBeVisible();
  });

  test("a property already in a neighbourhood cannot create another", async ({
    page,
  }) => {
    await page.setExtraHTTPHeaders({ "X-Mock-User-Id": MEMBER_USER_ID });
    await page.goto(
      `/dashboard/properties/${MEMBER_PROPERTY_ID}/neighbourhood/setup`,
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
