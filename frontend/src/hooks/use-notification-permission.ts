import { Capacitor } from "@capacitor/core";
import { useCallback, useEffect, useState } from "react";
import { PushNotifications, type PermissionStatus } from "@capacitor/push-notifications";

export type NotificationPermissionState = PermissionStatus["receive"] | "unsupported";

export function useNotificationPermission() {
	const [status, setStatus] = useState<NotificationPermissionState>("prompt");
	const [loading, setLoading] = useState(true);
	const [token, setToken] = useState<string | null>(null);
	const [registrationError, setRegistrationError] = useState<string | null>(null);


	const refresh = useCallback(async () => {
		setLoading(true);

		try {
			const result = await PushNotifications.checkPermissions();
			setStatus(result.receive);
			return result.receive;
		} finally {
			setLoading(false);
		}
	}, []);

	const request = useCallback(async () => {
		if (!Capacitor.isNativePlatform()) {
			return "unsupported" as NotificationPermissionState;
		}

		setLoading(true);

		try {
			const result = await PushNotifications.requestPermissions();
			setStatus(result.receive);
            if (result.receive === "granted"){
                // This is where the device is registered for push delivery
                await PushNotifications.register();
            }
			return result.receive;
		} finally {
			setLoading(false);
		}
	}, []);

	useEffect(() => {
		// eslint-disable-next-line react-hooks/set-state-in-effect
		refresh();
	}, [refresh]);

	useEffect(() => {
		const onVisible = () => {
			if (document.visibilityState === "visible"){
				refresh();
			}
		};
		document.addEventListener("visibilitychange", onVisible);

		return() => document.removeEventListener("visibilitychange", onVisible);
	}, []);

	useEffect(() => {
		const registrationListener = PushNotifications.addListener("registration", (result) => {
			setToken(result.value);
		});
		
		const errorListener = PushNotifications.addListener("registrationError", (err) => {
			setRegistrationError(err.error);
		});
		
		return () => {
			void registrationListener.then((handle) => handle.remove());
			void errorListener.then((handle) => handle.remove());
		}
		
	}, [])

	return { status, loading, refresh, request, token, registrationError };

}