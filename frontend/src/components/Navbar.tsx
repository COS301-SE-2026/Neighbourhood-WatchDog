"use client"

import { Bell, LogOut, Monitor, Moon, User, UserRound } from "lucide-react";
import Link from "next/link";
import { AvatarFallback, Avatar } from "@/components/ui/avatar";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { SidebarTrigger } from "./ui/sidebar";
import { useRouter } from "next/navigation";
import React from "react";
import { logout } from "@/lib/auth/cognito";

const Navbar = () => {
    const router = useRouter();

    const [username, setUsername] = React.useState("");

    React.useEffect(() => {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setUsername(localStorage.getItem("fullname") ?? "");
    }, []);

    const handleLogout = async () => {
        localStorage.removeItem("accessToken");
        localStorage.removeItem("idToken");
        localStorage.removeItem("fullname");

        logout();

        router.push("/auth/login");
    };

    return (
        <nav className="p-4 flex items-center text-white justify-between">
            <SidebarTrigger />

            <div className="flex items-center gap-4">
                <Link href="">Dashboard</Link>

                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Avatar>
                            <AvatarFallback className="bg-muted text-muted-foreground">
                                <User className="size-4" />
                            </AvatarFallback>
                        </Avatar>
                    </DropdownMenuTrigger>

                    <DropdownMenuContent align="end" className="w-56">
                        <DropdownMenuLabel>
                            <div className="flex flex-col">
                                <span className="text-sm font-medium">
                                    {username}
                                </span>

                                <span className="text-xs font-normal text-muted-foreground">
                                    Resident
                                </span>
                            </div>
                        </DropdownMenuLabel>

                        <DropdownMenuSeparator />

                        <DropdownMenuItem>
                            <UserRound className="mr-2 size-4" />
                            My profile
                        </DropdownMenuItem>

                        <DropdownMenuItem>
                            <Bell className="mr-2 size-4" />
                            Notifications
                        </DropdownMenuItem>

                        <DropdownMenuItem>
                            <Monitor className="mr-2 size-4" />
                            Appearance
                        </DropdownMenuItem>

                        <DropdownMenuSeparator />

                        <DropdownMenuItem
                            onClick={handleLogout}
                            className="text-destructive focus:text-destructive"
                        >
                            <LogOut className="mr-2 size-4" />
                            Sign out
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>
        </nav>
    );
};

export default Navbar;
