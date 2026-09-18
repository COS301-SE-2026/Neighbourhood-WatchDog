"use client"

import { useState } from "react"
import {
	AlertDialog,
	AlertDialogContent,
	AlertDialogHeader,
	AlertDialogTitle,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogCancel,
	AlertDialogAction,
} from "@/components/ui/alert-dialog"

import { useLocationPermission } from "@/hooks/use-location-permission"
import { NativeSettings, AndroidSettings, IOSSettings } from "capacitor-native-settings"


function openAppSettings() {
	NativeSettings.open({
		optionAndroid: AndroidSettings.ApplicationDetails,
		optionIOS: IOSSettings.App,
	})
}

interface LocationPermissionInterface {
	readonly open: boolean;
	readonly onOpenChange: (open: boolean) => void;
}

export function LocationPermissionDialog({
	open,
	onOpenChange,
}: LocationPermissionInterface ){
	const { status, request } = useLocationPermission();
	const [requesting, setRequesting] = useState(false);
	const permanentlyDenied = status === "denied";
	
	const handleAllow = async () => {
		if (permanentlyDenied){
			openAppSettings();
			return;
		}

		setRequesting(true);
		const result = await request();
		setRequesting(false);
		if (result === "granted") onOpenChange(false); 

	}

	return (
		<AlertDialog open={open} onOpenChange={onOpenChange}>
			<AlertDialogContent>
				<AlertDialogHeader>
					<AlertDialogTitle>Allow location access</AlertDialogTitle>
					<AlertDialogDescription>
						WatchDog uses your location to alert nearby neighbours of an alert,
						and to show the location of security officers. 
					</AlertDialogDescription>
				</AlertDialogHeader>
				<AlertDialogFooter>
					<AlertDialogCancel>Not now</AlertDialogCancel>
					<AlertDialogAction onClick={handleAllow} disabled={requesting}>
						{permanentlyDenied ? "Open Settings" : "Allow location access"}
					</AlertDialogAction>
				</AlertDialogFooter>
			</AlertDialogContent>
		</AlertDialog>
	)
}