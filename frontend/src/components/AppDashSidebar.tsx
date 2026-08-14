"use client";

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
    SidebarMenuItem,
} from "@/components/ui/sidebar";

import logoImage from "@/assets/images/logo-mark-only.svg";
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

import {
    BellRing,
    Building2,
    Camera,
    Check,
    ChevronDown,
    ClipboardList,
    History,
    House,
    LayoutDashboard,
    MapPin,
    Megaphone,
    Plus,
    User,
    UserPlus,
    type LucideIcon,
} from "lucide-react";

import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

type ContextRole = "Resident" | "Neighbourhood Admin" | null;

type PropertyContext = {
    id: string;
    propertyId: string;
    neighbourhoodId: string | null;
    name: string;
    address: string;
    role: ContextRole;
    icon: LucideIcon;

    // static permission flag for now.
    canRequestNeighbourhoodJoin: boolean;
};

type SidebarItemData = {
    title: string;
    url: string;
    icon: LucideIcon;
    badge?: number;
};

type SidebarGroupData = {
    label: string;
    items: SidebarItemData[];
};

const exampleContexts: PropertyContext[] = [
    {
        id: "greenfields-estate",
        propertyId: "greenfields-property-id",
        neighbourhoodId: "greenfields-neighbourhood-id",
        name: "Greenfields Estate",
        address: "45 Oak Avenue",
        role: "Resident",
        icon: MapPin,
        canRequestNeighbourhoodJoin: false,
    },
    {
        id: "test-neighbourhood",
        propertyId: "test-property-id",
        neighbourhoodId: "test-neighbourhood-id",
        name: "Test Neighbourhood",
        address: "123 Test Street",
        role: "Neighbourhood Admin",
        icon: Building2,
        canRequestNeighbourhoodJoin: false,
    },
    {
        id: "brook-street-property",
        propertyId: "brook-street-property-id",
        neighbourhoodId: null,
        name: "Brook Street Property",
        address: "1332 Brook Street",
        role: null,
        icon: House,
        canRequestNeighbourhoodJoin: true,
    },
];

function getSidebarGroups(
    activeContext: PropertyContext,
): SidebarGroupData[] {
    const propertyBaseUrl = `/dashboard-v2/properties/${activeContext.propertyId}`;

    const propertyItems: SidebarItemData[] = [
        {
            title: "My property",
            url: propertyBaseUrl,
            icon: House,
        },
        {
            title: "My cameras",
            url: `${propertyBaseUrl}/cameras`,
            icon: Camera,
        },
    ];

    // Standalone property: it has no neighbourhood_id.
    // Only show joining if this user can make a request for this property.
    if (activeContext.neighbourhoodId === null) {
        const groups: SidebarGroupData[] = [
            {
                label: "WORKSPACE",
                items: [
                    {
                        title: "Overview",
                        url: "/dashboard-v2",
                        icon: LayoutDashboard,
                    },
                    {
                        title: "Alert history",
                        url: `${propertyBaseUrl}/alerts`,
                        icon: History,
                    },
                ],
            },
            {
                label: "MY HOME",
                items: propertyItems,
            },
        ];

        if (activeContext.canRequestNeighbourhoodJoin) {
            groups.push({
                label: "NEIGHBOURHOOD",
                items: [
                    {
                        title: "Join a neighbourhood",
                        url: `${propertyBaseUrl}/neighbourhood/join`,
                        icon: UserPlus,
                    },
                    {
                        title: "Create a neighbourhood",
                        url: `${propertyBaseUrl}/neighbourhood/setup`,
                        icon: Building2,
                    }
                ],
            });
        }

        return groups;
    }

    // A property already belongs to a neighbourhood.
    // Therefore it should NEVER show "Join a neighbourhood".
    const groups: SidebarGroupData[] = [
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
                    url: `${propertyBaseUrl}/alerts`,
                    icon: History,
                },
                {
                    title: "Neighbourhood updates",
                    url: `/dashboard-v2/neighbourhoods/${activeContext.neighbourhoodId}/updates`,
                    icon: Megaphone,
                },
            ],
        },
        {
            label: "MY HOME",
            items: propertyItems,
        },
    ];

    // Only an admin for THIS active neighbourhood sees management actions.
    if (activeContext.role === "Neighbourhood Admin") {
        groups.push({
            label: "MANAGE NEIGHBOURHOOD",
            items: [
                {
                    title: "Join requests",
                    url: `/dashboard-v2/neighbourhoods/${activeContext.neighbourhoodId}/join-requests`,
                    icon: ClipboardList,
                    badge: 2,
                },
            ],
        });
    }

    return groups;
}

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
    );
}

const AppDashSidebar = () => {
    const [activeContext, setActiveContext] = useState<PropertyContext>(
        exampleContexts[0],
    );

    const ActiveContextIcon = activeContext.icon;

    const activeContextDescription =
        activeContext.neighbourhoodId === null
            ? `${activeContext.address} · Standalone property`
            : `${activeContext.address} · ${activeContext.role}`;

    const sidebarGroups = getSidebarGroups(activeContext);

    return (
        <Sidebar collapsible="icon">
            <SidebarHeader className="border-b border-sidebar-border px-3 py-3 group-data-[collapsible=icon]:px-2">
                <SidebarMenu>
                    <SidebarMenuItem>
                        <SidebarMenuButton
                            asChild
                            size="lg"
                            tooltip="Neighbourhood WatchDog"
                            className="group-data-[collapsible=icon]:justify-center"
                        >
                            <Link
                                href="/dashboard-v2"
                                className="flex items-center gap-3 group-data-[collapsible=icon]:justify-center"
                            >
                                <div className="flex size-9 shrink-0 items-center justify-center">
                                    <WatchdogLogo size={25} />
                                </div>

                                <div className="grid flex-1 text-left leading-tight group-data-[collapsible=icon]:hidden">
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

                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <button
                            type="button"
                            className="mt-3 flex w-full items-start gap-2.5 rounded-lg border border-white/10 bg-white/[0.03] p-3 text-left transition-colors hover:bg-white/[0.06] group-data-[collapsible=icon]:hidden"
                        >
                            <div className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-md bg-emerald-500/10">
                                <ActiveContextIcon className="size-3.5 text-emerald-400" />
                            </div>

                            <div className="min-w-0 flex-1">
                                <p className="text-[10px] font-medium uppercase tracking-wider text-white/40">
                                    Viewing
                                </p>

                                <p className="mt-1 truncate text-sm font-medium text-white">
                                    {activeContext.name}
                                </p>

                                <p className="mt-0.5 truncate text-xs text-white/50">
                                    {activeContextDescription}
                                </p>
                            </div>

                            <ChevronDown className="mt-1 size-4 shrink-0 text-white/40" />
                        </button>
                    </DropdownMenuTrigger>

                    <DropdownMenuContent
                        align="start"
                        side="bottom"
                        className="w-72 border-white/10 bg-zinc-950 p-1.5 text-white"
                    >
                        <DropdownMenuLabel className="px-2 py-2 text-xs font-medium uppercase tracking-wider text-white/40">
                            Switch location
                        </DropdownMenuLabel>

                        {exampleContexts.map((context) => {
                            const ContextIcon = context.icon;
                            const isActive =
                                context.id === activeContext.id;

                            const contextDescription =
                                context.neighbourhoodId === null
                                    ? `${context.address} · Standalone property`
                                    : `${context.address} · ${context.role}`;

                            return (
                                <DropdownMenuItem
                                    key={context.id}
                                    onSelect={() =>
                                        setActiveContext(context)
                                    }
                                    className={`flex cursor-pointer items-start gap-3 rounded-md px-2 py-2.5 focus:text-white ${
                                        isActive
                                            ? "bg-emerald-500/10 focus:bg-emerald-500/15"
                                            : "focus:bg-white/10"
                                    }`}
                                >
                                    <div
                                        className={`mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-md ${
                                            isActive
                                                ? "bg-emerald-500/15"
                                                : "bg-white/5"
                                        }`}
                                    >
                                        <ContextIcon
                                            className={`size-3.5 ${
                                                isActive
                                                    ? "text-emerald-400"
                                                    : "text-white/60"
                                            }`}
                                        />
                                    </div>

                                    <div className="min-w-0 flex-1">
                                        <p className="truncate text-sm font-medium">
                                            {context.name}
                                        </p>

                                        <p className="mt-0.5 truncate text-xs text-white/50">
                                            {contextDescription}
                                        </p>
                                    </div>

                                    {isActive && (
                                        <Check className="mt-1 size-4 shrink-0 text-emerald-400" />
                                    )}
                                </DropdownMenuItem>
                            );
                        })}

                        <DropdownMenuSeparator className="my-1 bg-white/10" />

                        <DropdownMenuItem className="cursor-pointer gap-2 rounded-md px-2 py-2.5 text-emerald-400 focus:bg-emerald-500/10 focus:text-emerald-300">
                            <Plus className="size-4" />
                            Add property
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </SidebarHeader>

            <SidebarContent>
                {sidebarGroups.map((group) => (
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

                                            {item.badge !== undefined && (
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

            <SidebarFooter className="border-t border-white/10 px-5 py-4 group-data-[collapsible=icon]:px-2">
                <div
                    title="Obed Edom Mbaya · Resident"
                    className="flex items-center gap-3 group-data-[collapsible=icon]:justify-center"
                >
                    <div className="flex size-9 shrink-0 items-center justify-center rounded-full border border-emerald-500/30 bg-emerald-500/10">
                        <User className="size-4 text-emerald-400" />
                    </div>

                    <div className="min-w-0 group-data-[collapsible=icon]:hidden">
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
    );
};

export default AppDashSidebar;