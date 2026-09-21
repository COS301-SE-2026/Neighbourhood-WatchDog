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

interface BackgroundLocationPermissionInterface {
	readonly open: boolean;
	readonly onOpenChange: (open: boolean) => void;
}

export function BackgroundLocationPermissionDialog({
	open,
	onOpenChange,
}: BackgroundLocationPermissionInterface) {
	const { requestBackground } = useLocationPermission();
	const [requesting, setRequesting] = useState(false);

	const handleContinue = async () => {
		setRequesting(true);
		await requestBackground();
		setRequesting(false);
		onOpenChange(false);
	}

	return (
		<AlertDialog open={open} onOpenChange={onOpenChange}>
			<AlertDialogContent>
				<AlertDialogHeader>
					<AlertDialogTitle>Keep sharing location in the background</AlertDialogTitle>
					<AlertDialogDescription>
						You will be taken to your phones&apos;s app settings. Tap 
						&quot;Permissions&quot; then &quot;Location&quot;, then choose
						&quot;Allow all the time&quot; so WatchDog can keep sharing your
						location while you&apos;re on duty, even if you switch apps.
					</AlertDialogDescription>
				</AlertDialogHeader>
				<AlertDialogFooter>
					<AlertDialogCancel>Not now</AlertDialogCancel>
					<AlertDialogAction onClick={handleContinue} disabled={requesting}>
						Continue to Settings
					</AlertDialogAction>
				</AlertDialogFooter>
			</AlertDialogContent>
		</AlertDialog>
	)
}