"use client";

import * as React from "react"
import Image from "next/image"
import {
  LayoutDashboard,
  User,
  ChevronDown,
  ChevronRight,
  Home,
  Pin,
  PinOff,
  Bell,
  FileText,
  Settings,
  ClipboardClock,
  KeyRound,
} from "lucide-react";
  Plus,
} from "lucide-react"

import { CreatePropertyDialog } from "./create-property-dialogue"
import { useEffect } from "react"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import { cn } from "@/lib/utils"
import { useProperties, type Property } from "@/hooks/use-properties"
import { useAppView } from "@/components/app-view-context"

// Types

type NavChild = {
  id: string;
  label: string;
  icon: React.ReactNode;
};

type NavItem = {
  id: string;
  label: string;
  icon: React.ReactNode;
  children?: NavChild[];
};

//data

const USERNAME = "John Doe";

const PROPERTIES: Property[] = [
  { id: "p1", name: "Oakwood Estate", address: "14 Oakwood Ave" },
  { id: "p2", name: "Sunset Heights", address: "7 Sunset Blvd" },
  { id: "p3", name: "Riverview Close", address: "3 Riverview Rd" },
];

/**
 * NAV_ITEMS drives every navigation tile in the sidebar.
 * To add a new tile: push a new entry here — no JSX changes needed.
 */
const NAV_ITEMS: NavItem[] = [
  {
    id: "dashboard",
    label: "Dashboard",
    icon: <LayoutDashboard className="h-4 w-4 shrink-0" />,
    children: PROPERTIES.map((p) => ({
      id: p.id,
      label: p.name,
      icon: <Home className="h-3.5 w-3.5 shrink-0" />,
    })),
  },
  {
    id: "requests",
    label: "Requests",
    icon: <ClipboardClock className="h-4 w-4 shrink-0" />,
  },
  {
    id: "alerts",
    label: "Alerts",
    icon: <Bell className="h-4 w-4 shrink-0" />,
  },
  {
    id: "reports",
    label: "Reports",
    icon: <FileText className="h-4 w-4 shrink-0" />,
  },
  {
    id: "joinNeighbourhood",
    label: "Join Neighbourhood",
    icon: <KeyRound className="h-4 w-4 shrink-0" />,
  },
  {
    id: "settings",
    label: "Settings",
    icon: <Settings className="h-4 w-4 shrink-0" />,
  },
];

// Logo
function WatchdogLogo({ size = 28 }: { size?: number }) {
  return (
    <Image
      src="/logo.png"
      width={size}
      height={size}
      alt=""
      aria-hidden="true"
      className="block object-contain"
    >
      <path
        d="M14 2L4 6v8c0 5.5 4.3 10.7 10 12 5.7-1.3 10-6.5 10-12V6L14 2z"
        fill="#3B5EDE"
        fillOpacity="0.25"
        stroke="#5B8DEF"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <ellipse
        cx="14"
        cy="13"
        rx="4.5"
        ry="3"
        fill="#5B8DEF"
        fillOpacity="0.3"
        stroke="#5B8DEF"
        strokeWidth="1.2"
      />
      <circle cx="14" cy="13" r="1.6" fill="#5B8DEF" />
      <path
        d="M10.5 18l2.5 2.5L18 15"
        stroke="#5B8DEF"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
    </Image>
  )
}

// Pin Button

function PinToggle({
  pinned,
  onToggle,
}: {
  pinned: boolean;
  onToggle: () => void;
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          onClick={onToggle}
          className={cn(
            "flex items-center justify-center rounded-md p-1.5",
            "transition-colors duration-150",
            pinned
              ? "text-[#5B8DEF] hover:text-white hover:bg-white/10"
              : "text-white/30 hover:text-white/70 hover:bg-white/10",
          )}
          aria-label={pinned ? "Unpin sidebar" : "Pin sidebar open"}
        >
          {pinned ? (
            <Pin className="h-3.5 w-3.5" />
          ) : (
            <PinOff className="h-3.5 w-3.5" />
          )}
        </button>
      </TooltipTrigger>
      <TooltipContent side="right">
        {pinned ? "Unpin: hover to expand" : "Pin sidebar open"}
      </TooltipContent>
    </Tooltip>
  );
}

// NavTile

function NavTile({
  item,
  activeSection,
  activeChild,
  onSelect,
  onChildSelect,
  isExpanded,
  onAddProperty, // TODO: if we decide to let the user add proeprties from elsewhere then we gotta remove this
}: {
  item: NavItem
  activeSection: string
  activeChild: string | null
  onSelect: (id: string) => void
  onChildSelect: (id: string) => void
  isExpanded: boolean
  onAddProperty?: () => void
}) {

  const isActive = activeSection === item.id
  const isOpen   = isActive && !!item.children

  const button = (
    <button
      onClick={() => onSelect(item.id)}
      className={cn(
        "flex w-full items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium",
        "transition-all duration-150",
        isActive
          ? "bg-[#1D2A5E] text-white shadow-[inset_0_0_0_1px_rgba(91,141,239,0.35)]"
          : "text-white/70 hover:bg-white/8 hover:text-white",
        !isExpanded && "justify-center px-2",
      )}
    >
      <span
        className={cn(
          "shrink-0",
          isActive ? "text-[#5B8DEF]" : "text-white/60",
        )}
      >
        {item.icon}
      </span>
      {isExpanded && (
        <>
          <span className="flex-1 truncate text-left">{item.label}</span>
          {item.children && (
            <ChevronDown
              className={cn(
                "h-3.5 w-3.5 shrink-0 text-white/40 transition-transform duration-200",
                isOpen && "rotate-180",
              )}
            />
          )}
        </>
      )}
    </button>
  );

  return (
    <SidebarMenuItem>
      {!isExpanded ? (
        <Tooltip>
          <TooltipTrigger asChild>{button}</TooltipTrigger>
          <TooltipContent side="right">{item.label}</TooltipContent>
        </Tooltip>
      ) : (
        button
      )}

      {/* Children dropdown — only when expanded */}
      {isExpanded && item.children && isOpen && (
        <ul className="mt-1 ml-4 overflow-hidden border-l border-white/10 pl-3 animate-in slide-in-from-top-1 fade-in duration-150">
          {item.children.map((child) => (
            <li key={child.id}>
              <button
                onClick={() => onChildSelect(child.id)}
                className={cn(
                  "flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-xs font-medium",
                  "transition-colors duration-100",
                  activeChild === child.id
                    ? "bg-[#1D2A5E] text-white shadow-[inset_0_0_0_1px_rgba(91,141,239,0.25)]"
                    : "text-white/55 hover:bg-white/8 hover:text-white/90",
                )}
              >
                <span
                  className={cn(
                    "shrink-0",
                    activeChild === child.id
                      ? "text-[#5B8DEF]"
                      : "text-white/40",
                  )}
                >
                  {child.icon}
                </span>
                <span className="truncate">{child.label}</span>
                {activeChild === child.id && (
                  <ChevronRight className="ml-auto h-3 w-3 text-[#5B8DEF]" />
                )}
              </button>
            </li>
          ))}
          {item.id === "dashboard" && onAddProperty && (
            <li>
              <button
                onClick={onAddProperty}
                className={cn(
                  "flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-xs font-medium",
                  "transition-colors duration-100",
                  "text-white/55 hover:bg-white/8 hover:text-white/90"
                  //this is temporary: use the variables when we refactor the whole thing's CSS
                )}
              >
                <span className="shrink-0 text-white/40">
                  <Plus className="h-3.5 w-3.5" />
                </span>
                <span className="truncate">Add Property</span>
              </button>
            </li>
          )}
        </ul>
      )}
    </SidebarMenuItem>
  );
}

// AppSidebar

export function AppSidebar() {
  const { state, setOpen } = useSidebar()
  const { properties, addProperty } = useProperties()
  const { section, propertyId, setSection, setPropertyView } = useAppView()

  // pinned = sidebar is locked open; unpinned = hover-to-expand mode
  const [pinned, setPinned] = React.useState(true)
  const [dialogOpen, setDialogOpen] = React.useState(false)

  const isExpanded = state === "expanded";

  const NAV_ITEMS: NavItem[] = [
    {
      id: "dashboard",
      label: "Dashboard",
      icon: <LayoutDashboard className="h-4 w-4 shrink-0" />,
      children: properties.map((p) => ({
        id: p.property_id,
        label: p.address,
        icon: <Home className="h-3.5 w-3.5 shrink-0" />,
      })),
    },
    {
      id: "alerts",
      label: "Alerts",
      icon: <Bell className="h-4 w-4 shrink-0" />,
    },
    {
      id: "reports",
      label: "Reports",
      icon: <FileText className="h-4 w-4 shrink-0" />,
    },
    {
      id: "settings",
      label: "Settings",
      icon: <Settings className="h-4 w-4 shrink-0" />,
    },
  ]

  const handlePropertyAdded = (property: Property) => {
    addProperty(property)
    setDialogOpen(false)
  }

  // When the user toggles the pin:
  // - Pinning: lock it open
  // - Unpinning: collapse it so hover mode takes over
  const handlePinToggle = () => {
    if (pinned) {
      setPinned(false);
      setOpen(false); // collapse — hover will re-expand temporarily
    } else {
      setPinned(true);
      setOpen(true); // lock open
    }
  };

  const handleMouseEnter = () => {
    if (!pinned) setOpen(true);
  };

  const handleMouseLeave = () => {
    if (!pinned) setOpen(false);
  };

  const handleSelect = (id: string) => {
    setSection(id as typeof section)
  }

  const handleChildSelect = (id: string) => {
    setPropertyView(id)
  }

  return (
    <Sidebar
      collapsible="icon"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Header */}
      <SidebarHeader className="px-3 py-3">
        <SidebarMenu>
          <SidebarMenuItem>
            <div
              className={cn(
                "flex items-center gap-2.5",
                !isExpanded && "justify-center",
              )}
            >
              {/* Logo mark — always visible */}
              <div className="shrink-0">
                <WatchdogLogo size={28} />
              </div>

              {/* Wordmark + pin will be visible when bar i s expanded */}
              {isExpanded && (
                <>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-extrabold text-white leading-tight tracking-tight truncate">
                      Neighbourhood
                    </p>
                    <p className="text-xs font-semibold text-[#5B8DEF] leading-tight tracking-widest uppercase truncate">
                      WatchDog
                    </p>
                  </div>
                  <div className="ml-auto shrink-0">
                    <PinToggle pinned={pinned} onToggle={handlePinToggle} />
                  </div>
                </>
              )}
            </div>

            {/* When collapsed, show pin below logo */}
            {!isExpanded && (
              <div className="mt-2 flex justify-center">
                <PinToggle pinned={pinned} onToggle={handlePinToggle} />
              </div>
            )}
          </SidebarMenuItem>
        </SidebarMenu>
        <div className="mt-3 h-px bg-white/10" />
      </SidebarHeader>


      <SidebarContent className="px-2 py-2">
        <SidebarGroup>
          <SidebarMenu>
            {NAV_ITEMS.map((item) => (
              <NavTile
                key={item.id}
                item={item}
                activeSection={section}
                activeChild={propertyId}
                onSelect={handleSelect}
                onChildSelect={handleChildSelect}
                isExpanded={isExpanded}
                onAddProperty={item.id === "dashboard" ? () => setDialogOpen(true) : undefined}
              />
            ))}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>

      <CreatePropertyDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onPropertyAdded={handlePropertyAdded}
      />

      <SidebarFooter className="px-3 py-3">
        <div className="h-px bg-white/10 mb-3" />
        <SidebarMenu>
          <SidebarMenuItem>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  className={cn(
                    "flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2",
                    "text-white/60 hover:text-white hover:bg-white/8 transition-colors duration-150",
                    !isExpanded && "justify-center",
                  )}
                >
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#3B5EDE]/40 ring-1 ring-[#5B8DEF]/40">
                    <User className="h-3.5 w-3.5 text-[#5B8DEF]" />
                  </span>
                  {isExpanded && (
                    <span className="truncate text-sm font-medium text-white/80">
                      {USERNAME}
                    </span>
                  )}
                </button>
              </TooltipTrigger>
              {!isExpanded && (
                <TooltipContent side="right">{USERNAME}</TooltipContent>
              )}
            </Tooltip>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
