"use client"

import { usePathname } from "next/navigation"
import { AppSidebar } from "@/components/app-sidebar"

export default function AppSidebarClient() {
  const pathname = usePathname() || ""

  // Hide the sidebar for the login page and any nested routes
  if (pathname.startsWith("/login-page")) return null

  return <AppSidebar />
}
