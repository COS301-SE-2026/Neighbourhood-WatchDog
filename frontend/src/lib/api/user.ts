import { apiCall } from "./client";

export async function registerPushDevice(deviceToken: string) {
  return apiCall<{ status: number; message: string }>("/users/me/push-device", {
		method: "POST",
		body: JSON.stringify({ device_token: deviceToken }),
	})
}