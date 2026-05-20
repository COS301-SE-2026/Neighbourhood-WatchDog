"use client"

import { LayoutDashboard, User } from "lucide-react"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from "@/components/ui/sidebar"

import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu"

const USERNAME = "John Doe"

export function AppSidebar() {
  return (
    <Sidebar className="bg-sidebar">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem className="text-white font-extrabold">
            <h1>Neighbourhood WatchDog</h1>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>  
        
      <SidebarContent>
        <SidebarGroup>
          <SidebarMenuButton className="text-white hover:bg-blue-600 hover:text-white transition duration-fast">
            <LayoutDashboard className="h-4 w-4" />
            Dashboard
          </SidebarMenuButton>
        </SidebarGroup>
        <SidebarGroup />
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton className="text-white">
              <User className="h-4 w-4"/>
              { USERNAME }
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  )
}