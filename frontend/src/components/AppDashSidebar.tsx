"use client"
import { 
    Sidebar, 
    SidebarContent, 
    SidebarFooter, 
    SidebarGroup, 
    SidebarGroupContent, 
    SidebarGroupLabel, 
    SidebarHeader, 
    SidebarMenu, 
    SidebarMenuBadge, 
    SidebarMenuButton, 
    SidebarMenuItem 
} from "@/components/ui/sidebar";

import logoImage from "@/assets/images/logo-mark-only.svg"
import Image from "next/image"


import {
    BellRing,
    Camera,
    History,
    House,
    LayoutDashboard,
    Megaphone,
    Settings,
    User,
} from "lucide-react";
import Link from "next/link";

const residentSidebarGroups = [
    {
        label: "WORKSPACE",
        items: [
            {
                title: "Overview",
                url: "/dashboard-v2",
                icon: LayoutDashboard,
            },
            {
                title: "Live alerts",
                url: "/dashboard-v2",
                icon: BellRing,
                badge: 3,
            },
            {
                title: "Alert history",
                url: "/dashboard-v2",
                icon: History,
            },
            {
                title: "Neighbourhood updates",
                url: "/dashboard-v2",
                icon: Megaphone,
            },
        ],
    },
    {
        label: "MY HOME",
        items: [
            {
                title: "My property",
                url: "/dashboard-v2",
                icon: House,
            },
            {
                title: "My cameras",
                url: "/dashboard-v2",
                icon: Camera,
            },
        ],
    },
];


function WatchdogLogo({ size = 28 }: { size?: number }) {
  return (
    <Image
      src={logoImage}
      width={size}
      height={size}
      alt=""
      aria-hidden="true"
      className="block object-contain"
    />
  )
}


const AppDashSidebar = () => {
    return (
        <Sidebar>
            <SidebarHeader className="border-b border-sidebar-border px-3 py-3">
                <SidebarMenu>
                    <SidebarMenuItem>
                        <SidebarMenuButton
                            asChild
                            size="lg"
                            tooltip="Neighbourhood WatchDog"
                        >
                            <Link
                                href="/dashboard-v2"
                                className="flex items-center gap-3"
                            >
                                <div className="flex size-9 items-center justify-center">
                                    <WatchdogLogo size={25} />
                                </div>

                                <div className="grid flex-1 text-left leading-tight">
                                    <span className="text-sm font-semibold tracking-tight text-sidebar-foreground">
                                        Neighbourhood
                                    </span>

                                    <span className="text-sm font-semibold tracking-tight text-sidebar-foreground">
                                        WatchDog
                                    </span>
                                </div>
                            </Link>
                        </SidebarMenuButton>
                    </SidebarMenuItem>
                </SidebarMenu>
            </SidebarHeader>

            <SidebarContent>
                {residentSidebarGroups.map((group) => (
                    <SidebarGroup key={group.label}>
                        <SidebarGroupLabel>
                            {group.label}
                        </SidebarGroupLabel>

                        <SidebarGroupContent>
                            <SidebarMenu>
                                {group.items.map((item) => {
                                    const Icon = item.icon;

                                    return (
                                        <SidebarMenuItem key={item.title}>
                                            <SidebarMenuButton asChild>
                                                <Link href={item.url}>
                                                    <Icon />
                                                    <span>{item.title}</span>
                                                </Link>
                                            </SidebarMenuButton>

                                            {item.badge && (
                                                <SidebarMenuBadge>
                                                    {item.badge}
                                                </SidebarMenuBadge>
                                            )}
                                        </SidebarMenuItem>
                                    );
                                })}
                            </SidebarMenu>
                        </SidebarGroupContent>
                    </SidebarGroup>
                ))}
            </SidebarContent>

            <SidebarFooter className="border-t border-white/10 px-5 py-4">
                <div className="flex items-center gap-3">
                    <div className="flex size-9 shrink-0 items-center justify-center rounded-full border border-emerald-500/30 bg-emerald-500/10">
                        <User className="size-4 text-emerald-400" />
                    </div>

                    <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-white">
                            Obed Edom Mbaya
                        </p>

                        <p className="mt-0.5 truncate text-xs text-white/50">
                            Resident
                        </p>
                    </div>
                </div>
            </SidebarFooter>
        </Sidebar>
    )
}

export default AppDashSidebar;