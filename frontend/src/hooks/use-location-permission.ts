import { useCallback, useEffect, useState } from "react";
import { Capacitor } from "@capacitor/core";
import { Geolocation, type PermissionStatus } from "@capacitor/geolocation";

export type LocationPermissionState = PermissionStatus["location"] | "unsupported";

export function useLocationPermission() {
	const [status, setStatus] = useState<LocationPermissionState>("prompt");
	const [loading, setLoading] = useState(true);

	const refresh = useCallback(async () => {
		if (!Capacitor.isNativePlatform()) {
		
			setStatus("unsupported");
			setLoading(false);
			return "unsupported" as LocationPermissionState;
		
		}

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
		refresh();
	}, [refresh]);


	return { status, loading, refresh, request }

}