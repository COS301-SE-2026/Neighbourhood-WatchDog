import { test as base } from "@playwright/test";

export const NEIGHBOURHOOD_ID = "10000000-0000-0000-0000-000000000001";
export const ADMIN_USER_ID = "20000000-0000-0000-0000-000000000001";
export const RESIDENT_USER_ID = "20000000-0000-0000-0000-000000000002";
export const OFFICER_USER_ID = "20000000-0000-0000-0000-000000000003";
export const DENY_FLOW_USER_ID = "20000000-0000-0000-0000-000000000004";

export const PROPERTY_ID = "30000000-0000-0000-0000-000000000001";
export const PENDING_PROPERTY_ID = "30000000-0000-0000-0000-000000000002";
export const FREE_PROPERTY_ID = "30000000-0000-0000-0000-000000000003";
export const OFFICER_PROPERTY_ID = "30000000-0000-0000-0000-000000000003";
export const CREATE_PROPERTY_ID = "30000000-0000-0000-0000-000000000005";
export const CREATE_USER_ID = "20000000-0000-0000-0000-000000000005";
export const MEMBER_PROPERTY_ID = PROPERTY_ID;
export const MEMBER_USER_ID = ADMIN_USER_ID;

export const CAMERA_ID = "40000000-0000-0000-0000-000000000001";
export const SECOND_CAMERA_ID = "40000000-0000-0000-0000-000000000002";
export const ALERT_ID = "80000000-0000-0000-0000-000000000001";
export const PAIRING_TOKEN = "e2e-pairing-token-001";

export const test = base.extend({
  page: async ({ page }, use) => {
    await page.setExtraHTTPHeaders({
      Authorization: "Bearer mocktake",
      "X-Mock-User-Id": ADMIN_USER_ID,
    });

    await page.addInitScript(() => {
      localStorage.setItem("accessToken", "mocktake");
    });

    await use(page);
  },
});

export { expect } from "@playwright/test";
