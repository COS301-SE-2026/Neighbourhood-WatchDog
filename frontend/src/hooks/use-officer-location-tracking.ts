"use client"

import { useEffect, useRef } from "react"
import { Geolocation } from "@capacitor/geolocation"
import { updateSecurityLocation } from "@/lib/api/neighbourhood"

const LOCATION_PUSH_INTERVAL_MS = 30_000

export function useOfficerLocationTracking(
	neighbourhoodId: string,
	onDuty: boolean,
){
	const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

	useEffect(() => {
		if (!onDuty) return

		const pushLocation = async () => {
			try {
				const pos = await Geolocation.getCurrentPosition({
					enableHighAccuracy: true,
					timeout: 10_000,
				})
				await updateSecurityLocation({
					neighbourhood_id: neighbourhoodId, 
					latitude: pos.coords.latitude, 
					longitude: pos.coords.longitude,
				})
			} catch (err) {
				const locationError = err as {
					code?: number;
					message?: string;
				};

				console.error("Failed to push officer location", {
					code: locationError.code,
					message: locationError.message,
					error: err,
				});
				}

		}
		pushLocation()
		intervalRef.current = setInterval(pushLocation, LOCATION_PUSH_INTERVAL_MS)
		
		return () => {
			if (intervalRef.current) clearInterval(intervalRef.current)
		}
	}, [neighbourhoodId, onDuty])

}