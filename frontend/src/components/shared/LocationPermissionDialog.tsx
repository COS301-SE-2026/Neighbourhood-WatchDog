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
	const [requesting, setRequesting] = useState(false);
	
	const handleAllow = async () => {
		setRequesting(true);
		await NativeSettings.open({
			optionAndroid: AndroidSettings.ApplicationDetails,
			optionIOS: IOSSettings.App,
		})
		setRequesting(false);
	}

	return (
		<AlertDialog open={open} onOpenChange={onOpenChange}>
			<AlertDialogContent>
				<AlertDialogHeader>
					<AlertDialogTitle>Allow location access</AlertDialogTitle>
					<AlertDialogDescription>
						To go on duty, you must allow background location permissions. <br/>
						This will allow WatchDog to use your location even when the app is not open. But only when you are <b>on duty</b> <br/>
						To do that, click on 'Open Settings'. Select permissions. Location permissions and select 'Allow all the time'.
					</AlertDialogDescription>
				</AlertDialogHeader>
				<AlertDialogFooter>
					<AlertDialogCancel>Not now</AlertDialogCancel>
					<AlertDialogAction onClick={handleAllow} disabled={requesting}>
						Open Settings
					</AlertDialogAction>
				</AlertDialogFooter>
			</AlertDialogContent>
		</AlertDialog>
	)
}