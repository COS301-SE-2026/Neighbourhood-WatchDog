import { test, expect, PROPERTY_ID } from "./fixtures";

test.describe("Pairing token and edge agent", () => {
  test("generates and displays a pairing token", async ({ page }) => {
    await page.goto(`/dashboard/properties/${PROPERTY_ID}/agent`);

    await expect(
      page.getByRole("heading", { name: "Connect an edge agent" }),
    ).toBeVisible();
    const token = await page.locator("p.font-mono").textContent();
    expect(token).toMatch(
      /^[23456789A-HJ-NP-Z]{3}(?:-[23456789A-HJ-NP-Z]{3}){2}$/,
    );

    const apiBaseUrl =
      process.ENV.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const res = await page.request.get(
      `${apiBaseUrl}/pairing-token/${encodeURIComponent(token ?? "")}`,
    );
    expect(res.status()).toBe(201);
    const resBody = await res.json();
    expect(resBody.data.property_id).toBe(PROPERTY_ID);
  });
});
