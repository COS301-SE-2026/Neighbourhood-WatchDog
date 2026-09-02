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
import { usePathname } from "next/navigation";
import Link from "next/link";
import { useState } from "react";

import { CreatePropertyDialog } from "./property-components/create-property-dialogue";

import {
    BellRing,
    Building2,
    Camera,
    ChartNoAxesCombined,
    Check,
    ChevronDown,
    ClipboardList,
    FileText,
    House,
    KeyRound,
    Plus,
    Settings,
    SlidersHorizontal,
    User,
    UserPlus,
    Users,
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

import { usePropertyContext, type PropertyContext } from "@/hooks/use-property-context";
import { useAuth } from "@/lib/auth/auth-context";
import { useUserContext } from "@/hooks/use-user-context";

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

function SidebarSkeleton() {
    return (
        <Sidebar collapsible="icon">
            <SidebarHeader>
                <div className="flex items-center gap-3 px-1 py-2">
                    <div className="size-9 shrink-0 rounded-md bg-white/5 animate-pulse" />
                    <div className="h-4 w-32 rounded bg-white/5 animate-pulse" />
                </div>
                <div className="mt-3 h-16 w-full rounded-lg bg-white/[0.03] animate-pulse" />
            </SidebarHeader>
            <SidebarContent>
                <div className="space-y-2 px-3 py-4">
                    {Array.from({ length: 5 }).map((_, i) => (
                        <div key={i} className="h-8 w-full rounded-md bg-white/5 animate-pulse" />
                    ))}
                </div>
            </SidebarContent>
        </Sidebar>
    )
}

function getSidebarGroups(
    activeContext: PropertyContext,
    systemRole: string | null,
): SidebarGroupData[] {
    const propertyBaseUrl = `/dashboard/properties/${activeContext.propertyId}`;

    const groups: SidebarGroupData[] = [
        {
            label: "MY HOME",
            items: [
                {
                    title: "My cameras",
                    url: `${propertyBaseUrl}/cameras`,
                    icon: Camera,
                },
                {
                    title: "Property alerts",
                    url: `${propertyBaseUrl}/alerts`,
                    icon: BellRing,
                },

                {
                    title: "Connect agent",
                    url: `${propertyBaseUrl}/agent`,
                    icon: KeyRound, 
                },
            ],
        },
    ];

    if (activeContext.neighbourhoodId === null) {
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
                    },
                ],
            });
        }

        addAccountGroup(groups);
        return addSystemAdminGroup(groups, systemRole);
    }

    const neighbourhoodItems: SidebarItemData[] = [
        {
            title: "Analytics",
            url: `/dashboard/neighbourhood/${activeContext.neighbourhoodId}/analytics`,
            icon: ChartNoAxesCombined,
        },
    ];

    if (
        activeContext.role === "Neighbourhood Admin" ||
        activeContext.role === "Security Officer"
    ) {
        neighbourhoodItems.unshift({
            title:
                activeContext.role === "Security Officer"
                    ? "Critical alerts"
                    : "Live alerts",
            url: `/dashboard/neighbourhood/${activeContext.neighbourhoodId}/alerts`,
            icon: BellRing,
            badge: 3,
        });
    }


    groups.push({
        label: "NEIGHBOURHOOD",
        items: neighbourhoodItems
    });

    if (activeContext.role === "Neighbourhood Admin") {
        groups.push({
            label: "MANAGE NEIGHBOURHOOD",
            items: [
                {
                    title: "Members",
                    url: `/dashboard/neighbourhood/${activeContext.neighbourhoodId}/members`,
                    icon: Users,
                },
                {

                    title: "Join requests",
                    url: `/dashboard/neighbourhood/${activeContext.neighbourhoodId}/join-requests`,
                    icon: ClipboardList,
                    badge: 2,
                },
                {
                    title: "Risk thresholds",
                    url: `/dashboard/neighbourhood/${activeContext.neighbourhoodId}/risk-threshold`,
                    icon: SlidersHorizontal,
                }
            ],
        });
    }

    addAccountGroup(groups);
    return addSystemAdminGroup(groups, systemRole);
}

function addSystemAdminGroup(groups: SidebarGroupData[], systemRole: string | null) {
    if (systemRole === "SYSTEM_ADMIN") {
        groups.push({
            label: "SYSTEM",
            items: [
                {
                    title: "Audit log",
                    url: "/dashboard/admin/audit",
                    icon: FileText,
                },
            ],
        });
    }
    return groups;
}

function addAccountGroup(groups: SidebarGroupData[]) {
    groups.push({
        label: "ACCOUNT",
        items: [
            {
                title: "Settings",
                url: "/dashboard/settings",
                icon: Settings,
            },
        ],
    });

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
    
    const {contexts, activeContext, isLoading, selectContext} = usePropertyContext();
    const pathname = usePathname();
    const { user: authUser } = useAuth();
    const { data: userContext } = useUserContext();
    const systemRole = userContext?.user.system_role ?? null;

    const [dialogOpen, setDialogOpen] = useState(false);
    const handlePropertyAdded = async () => {
        setDialogOpen(false);
        window.location.reload();
    };


    if (isLoading) {
        return <SidebarSkeleton />;
    }

    const ActiveContextIcon = activeContext?.icon ?? House;

    const activeContextDescription = activeContext
        ? activeContext.neighbourhoodId === null
            ? `${activeContext.address} - Standalone property`
            : `${activeContext.address} - ${activeContext.role}`
        : "Create a property to get started";

    const sidebarGroups = activeContext
        ? getSidebarGroups(activeContext, systemRole)
        : [
            {
                label: "ACCOUNT",
                items: [
                    {
                        title: "Settings",
                        url: "/dashboard/settings",
                        icon: Settings,
                    },
                ],
            },
        ];

    const footerContextLabel = activeContext
        ? activeContext.neighbourhoodId === null
            ? "Standalone property"
            : activeContext.role ?? "Resident"
        : "No property yet";


    
    return (
        <>
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
                                    href="/dashboard"
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

                    {activeContext ? (
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

                                {contexts.map((context) => {
                                    const ContextIcon = context.icon;
                                    const isActive = context.id === activeContext.id;

                                    const contextDescription =
                                        context.neighbourhoodId === null
                                            ? `${context.address} · Standalone property`
                                            : `${context.address} · ${context.role}`;

                                    return (
                                        <DropdownMenuItem
                                            key={context.id}
                                            onSelect={() => selectContext(context)}
                                            className={`flex cursor-pointer items-start gap-3 rounded-md px-2 py-2.5 focus:text-white ${
                                                isActive
                                                    ? "bg-emerald-500/10 focus:bg-emerald-500/15"
                                                    : ""
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

                                <DropdownMenuItem
                                    onSelect={() => setDialogOpen(true)}
                                    className="cursor-pointer gap-2 rounded-md px-2 py-2.5 text-emerald-400 focus:bg-emerald-500/10 focus:text-emerald-300"
                                >
                                    <Plus className="size-4" />
                                    Add property
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    ) : (
                        <button
                            type="button"
                            onClick={() => setDialogOpen(true)}
                            className="mt-3 w-full rounded-lg border border-emerald-500/20 bg-emerald-500/[0.06] p-3 text-left transition-colors hover:bg-emerald-500/[0.1] group-data-[collapsible=icon]:hidden"
                        >
                            <p className="text-sm font-medium text-white">
                                Create your first property
                            </p>

                            <p className="mt-1 text-xs text-white/50">
                                Add a property to start using WatchDog.
                            </p>
                        </button>
                    )}

                                                    
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
                                        const isActive = pathname === item.url;
                                        return (
                                            <SidebarMenuItem key={item.title}>
                                                <SidebarMenuButton asChild isActive={isActive}>
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
                        title={`${authUser?.fullname ?? ""}`}
                        className="flex items-center gap-3 group-data-[collapsible=icon]:justify-center"
                    >
                        <div className="flex size-9 shrink-0 items-center justify-center rounded-full border border-emerald-500/30 bg-emerald-500/10">
                            <User className="size-4 text-emerald-400" />
                        </div>
                        <div className="min-w-0 group-data-[collapsible=icon]:hidden">
                            <p className="truncate text-sm font-medium text-white">
                                {authUser?.fullname}
                            </p>


                            <p className="truncate text-[11px] text-white/35">
                                {footerContextLabel}
                            </p>

                        </div>
                    </div>
                </SidebarFooter>
            </Sidebar>
            <CreatePropertyDialog
                open={dialogOpen}
                onOpenChange={setDialogOpen}
                onPropertyAdded={handlePropertyAdded}
            />
        </>

    );
};

export default AppDashSidebar;