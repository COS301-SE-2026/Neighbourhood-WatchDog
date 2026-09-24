import { apiCall } from "./client";

export async function registerPushDevice(deviceToken: string) {
  return apiCall<{ status: number; message: string }>("/users/me/push-device", {
		method: "POST",
		body: { device_token: deviceToken },
	})
}