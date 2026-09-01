import { apiCall } from "./client";
import {
  type UpdateUserSettingsPayload,
  type UserSettingsRes,
} from "../validators/user";

const USER_SETTINGS_PATH = "/users/me/settings";
export async function fetchUserSettings(): Promise<UserSettingsRes> {
  const url = USER_SETTINGS_PATH;

  return await apiCall<UserSettingsRes>(url, {
    method: "GET",
  });
}

export async function updateUserSettings(
  data: UpdateUserSettingsPayload,
): Promise<UserSettingsRes> {
  const url = USER_SETTINGS_PATH;

  return await apiCall<UserSettingsRes>(url, {
    method: "PATCH",
    body: data,
  });
}
