"use client";

import { Bell, LogOut, Monitor, User, UserRound } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import React from "react";
import { useUserContext } from "@/hooks/use-user-context";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { AUTH_EVENT, logout } from "@/lib/auth/cognito";
import { SidebarTrigger } from "./ui/sidebar";

const Navbar = () => {
    const router = useRouter();
    const [username, setUsername] = React.useState("");
    const { data: userContext } = useUserContext();
    const displayName = userContext?.user.name ?? username;
    React.useEffect(() => {
        const syncUsername = () => {
            setUsername(localStorage.getItem("fullname") ?? "");
        };

        syncUsername();
        window.addEventListener(AUTH_EVENT, syncUsername);

        return () => {
            window.removeEventListener(AUTH_EVENT, syncUsername);
        };
    }, []);

    const handleLogout = async () => {
        localStorage.removeItem("accessToken");
        localStorage.removeItem("idToken");
        localStorage.removeItem("fullname");

        logout();
        router.push("/auth/login");
    };

    return (
        <nav className="flex items-center justify-between p-4 text-brand-frost">
            <SidebarTrigger />

            <div className="flex items-center gap-4">
                <Link href="/dashboard/help">Help</Link>
                <Link href="">Dashboard</Link>

                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <button
                            type="button"
                            aria-label="Open account menu"
                            title="Open account menu"
                            className="rounded-full"
                        >
                            <Avatar aria-hidden="true">
                                <AvatarFallback className="bg-muted text-muted-foreground">
                                    <User
                                        aria-hidden="true"
                                        className="size-4"
                                    />
                                </AvatarFallback>
                            </Avatar>
                        </button>
                    </DropdownMenuTrigger>

                    <DropdownMenuContent align="end" className="w-56">
                        <DropdownMenuLabel>
                            <div className="flex flex-col">
                                <span className="text-sm font-medium">
                                    {displayName}
                                </span>

                                <span className="text-xs font-normal text-muted-foreground">
                                    Resident
                                </span>
                            </div>
                        </DropdownMenuLabel>

                        <DropdownMenuSeparator />

                        <DropdownMenuItem onSelect={() => router.push("/dashboard/settings")}>
                            <UserRound
                                aria-hidden="true"
                                className="mr-2 size-4"
                            />
                            My Profile
                        </DropdownMenuItem>

                        <DropdownMenuItem>
                            <Bell
                                aria-hidden="true"
                                className="mr-2 size-4"
                            />
                            Notifications
                        </DropdownMenuItem>

                        <DropdownMenuItem>
                            <Monitor
                                aria-hidden="true"
                                className="mr-2 size-4"
                            />
                            Appearance
                        </DropdownMenuItem>

                        <DropdownMenuSeparator />

                        <DropdownMenuItem
                            onClick={handleLogout}
                            className="text-destructive focus:text-destructive"
                        >
                            <LogOut
                                aria-hidden="true"
                                className="mr-2 size-4"
                            />
                            Sign out
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>
        </nav>
    );
};

export default Navbar;