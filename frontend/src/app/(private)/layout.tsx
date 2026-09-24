"use client";

import { useEffect } from "react";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import { useNotificationPermission } from "@/hooks/use-notification-permission";
import { registerPushDevice } from "@/lib/api/user";
import { toast } from "sonner";


export default function ProtectedLayout({
	children,
}: {
	readonly children: React.ReactNode;
}) {
	const { isLoading, isLoggedIn } = useRequireAuth();
	const { request, token } = useNotificationPermission();

	useEffect(() => {
		if (isLoggedIn) request();
	}, [isLoggedIn, request]);

	useEffect(() => {
		if (token){
			registerPushDevice(token).catch((err) => {
				toast.error("Failed to enable push notifications.");
			});
		}
	}, [token]);

	if (isLoading || !isLoggedIn) {
		return null;
	}

	return <>{children}</>;
}