import { useCallback, useEffect, useState } from "react";
import { Capacitor } from "@capacitor/core";
import { Geolocation, type PermissionStatus } from "@capacitor/geolocation";
import { BackgroundGeolocation, type BackgroundLocationPermissionState } from "@capgo/background-geolocation";
import { NativeSettings, AndroidSettings, IOSSettings } from "capacitor-native-settings";

export type LocationPermissionState = PermissionStatus["location"] | "unsupported";
export type BackgroundPermissionState = BackgroundLocationPermissionState | "unsupported";

const BACKGROUND_GRANTED_STATES: BackgroundPermissionState[] = ["granted", "always"];

export function useLocationPermission() {
	const [status, setStatus] = useState<LocationPermissionState>("prompt");
	const [backgroundStatus, setBackgroundStatus] = useState<BackgroundPermissionState>("prompt");
	const [loading, setLoading] = useState(true);
	const [backgroundError, setBackgroundError] = useState<string | null>(null);

	const refresh = useCallback(async () => {
		setLoading(true);

		try {
			const result = await Geolocation.checkPermissions();
			setStatus(result.location);
			return result.location;
		} finally {
			setLoading(false);
		}
	}, []);

	const request = useCallback(async () => {
		if (!Capacitor.isNativePlatform()) {

			return "unsupported" as LocationPermissionState;
		
		}
		
		setLoading(true);

		try {
			const result = await Geolocation.requestPermissions({
				permissions: ["location", "coarseLocation"],
			});
			setStatus(result.location);
			return result.location;
		} finally {
			setLoading(false);
		}
	}, []);

	const requestBackground = useCallback(async () => {
		if (!Capacitor.isNativePlatform() || status !== "granted"){
			return "unsupported" as BackgroundPermissionState;
		}

		setLoading(true);
		setBackgroundError(null);
		try {
			const result = await BackgroundGeolocation.requestPermissions({
				permissions: ["backgroundLocation"],
			});
			const resolved: BackgroundPermissionState = result.backgroundLocation ?? "unsupported";

			if (!BACKGROUND_GRANTED_STATES.includes(resolved) && Capacitor.getPlatform() === "android"){
				await NativeSettings.open({
					optionAndroid: AndroidSettings.ApplicationDetails,
					optionIOS: IOSSettings.App,
				})
			}

			setBackgroundStatus(resolved);
			return resolved;
		} catch(err) {
			setBackgroundError(err instanceof Error ? err.message : "Failed to request background location permission");
			return "unsupported" as BackgroundPermissionState;
		} finally {
			setLoading(false);
		}
	}, [status]);

	useEffect(() => {
		// eslint-disable-next-line react-hooks/set-state-in-effect
		refresh();
	}, [refresh]);

	useEffect(() => {
		const onVisible = () => {
			if (document.visibilityState === "visible"){
				BackgroundGeolocation.checkPermissions().then((result) => {
					setBackgroundStatus(result.backgroundLocation ?? "unsupported");
				});
			}
		};
		document.addEventListener("visibilitychange", onVisible);

		return() => document.removeEventListener("visibilitychange", onVisible);
	}, []);

	return { status, backgroundStatus, loading, backgroundError, refresh, request, requestBackground }

}