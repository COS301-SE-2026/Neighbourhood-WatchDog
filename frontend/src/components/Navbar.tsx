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

const Navbar = () => {
    return (
        <nav className="p-4 flex items-center justify-between">
            collapseButton
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
                            <span className="text-sm font-medium">Obed Mbaya</span>
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

                        <DropdownMenuItem className="text-destructive focus:text-destructive">
                            <LogOut className="mr-2 size-4" />
                            Sign out
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                    </DropdownMenu>
            </div>
        </nav>
    )
}

export default Navbar;