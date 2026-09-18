import { useCallback, useEffect, useState } from "react";
import { Capacitor } from "@capacitor/core";
import { Geolocation, type PermissionStatus } from "@capacitor/geolocation";

export type LocationPermissionState = PermissionStatus["location"] | "unsupported";

export function useLocationPermission() {
	const [status, setStatus] = useState<LocationPermissionState>("prompt");
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


	useEffect(() => {
		// eslint-disable-next-line react-hooks/set-state-in-effect
		refresh();
	}, [refresh]);


	return { status, loading, refresh, request }

}