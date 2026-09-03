import { test, expect, NEIGHBOURHOOD_ID, ADMIN_USER_ID } from "./fixtures";

test.describe("Join Requests", () => {
  test("lists the pending requests", async ({ page }) => {
    await page.setExtraHTTPHeaders({ "X-Mock-User-Id": ADMIN_USER_ID });
    await page.goto(
      `/dashboard/neighbourhood/${NEIGHBOURHOOD_ID}/join-requests`,
    );

    await page.waitForSelector('[role="article"]', { timeout: 30000 });

    await expect(
      page.getByRole("article", { name: /join request from resident/i }),
    ).toBeVisible();
  });

  test("approving request moves it out of pending tab", async ({ page }) => {
    await page.setExtraHTTPHeaders({ "X-Mock-User-Id": ADMIN_USER_ID });
    await page.goto(
      `/dashboard/neighbourhood/${NEIGHBOURHOOD_ID}/join-requests`,
    );

    const card = page.getByRole("article", {
      name: /join request from resident/i,
    });
    await card.getByRole("button", { name: /approve/i }).click();

    await expect(card).not.toBeVisible();

    await page.getByRole("tab", { name: /^approved/i }).click();

    await expect(
      page.getByRole("article", { name: /join request from resident/i }),
    ).toContainText("Approved");
  });

  test("denying a request moves it out of pending tab", async ({ page }) => {
    await page.setExtraHTTPHeaders({ "X-Mock-User-Id": ADMIN_USER_ID });
    await page.goto(
      `/dashboard/neighbourhood/${NEIGHBOURHOOD_ID}/join-requests`,
    );

    const card = page.getByRole("article", {
      name: /join request from denyflow/i,
    });
    await card.getByRole("button", { name: /deny/i }).click();

    await page.getByRole("tab", { name: /^denied/i }).click();

    await expect(
      page.getByRole("article", { name: /join request from denyflow/i }),
    ).toContainText("Denied");
  });

  test("non admin cannot view join-requests page", async ({ page }) => {
    await page.setExtraHTTPHeaders({ "X-Mock-User-Id": RESIDENT_USER_ID });
    await page.goto(
      `/dashboard/neighbourhood/${NEIGHBOURHOOD_ID}/join-requests`,
    );

    await expect(
      page.getByText("You don't have admin access to this neighbourhood."),
    ).toBeVisible();
  });

  test("regenerating the join code changes displayed code", async ({
    page,
  }) => {
    await page.setExtraHTTPHeaders({ "X-Mock-User-Id": ADMIN_USER_ID });
    await page.goto(
      `/dashboard/neighbourhood/${NEIGHBOURHOOD_ID}/join-requests`,
    );

    const codeEl = page.locator("code");
    await expect(codeEl).not.toHaveText("Unavailable");
    const originalCode = await codeEl.textContent();

    await page.getByTitle("regenrates join code").click();

    await expect(codeEl).not.toHaveText(originalCode ?? "");
  });
});
