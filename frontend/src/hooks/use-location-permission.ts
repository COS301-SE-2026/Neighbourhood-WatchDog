import { useCallback, useEffect, useState } from "react";
import { Capacitor } from "@capacitor/core";
import { Geolocation, type PermissionStatus } from "@capacitor/geolocation";
import { BackgroundGeolocation, type BackgroundLocationPermissionState } from "@capgo/background-geolocation";

export type LocationPermissionState = PermissionStatus["location"] | "unsupported";
export type BackgroundPermissionState = BackgroundLocationPermissionState | "unsupported";

export function useLocationPermission() {
	const [status, setStatus] = useState<LocationPermissionState>("prompt");
	const [backgroundStatus, setBackgroundStatus] = useState<BackgroundPermissionState>("prompt");
	const [loading, setLoading] = useState(true);

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
		try {
			const result = await BackgroundGeolocation.requestPermissions({
				permissions: ["backgroundLocation"],
			});
			const resolved: BackgroundPermissionState = result.backgroundLocation ?? "unsupported";
			setBackgroundStatus(resolved);
			return resolved;
		} finally {
			setLoading(false);
		}
	}, [status]);

	useEffect(() => {
		// eslint-disable-next-line react-hooks/set-state-in-effect
		refresh();
	}, [refresh]);


	return { status, backgroundStatus, loading, refresh, request, requestBackground }

}