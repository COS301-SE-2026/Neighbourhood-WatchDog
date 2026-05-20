"use client"

import { usePathname } from "next/navigation"
import { AppSidebar } from "@/components/app-sidebar"

const HIDE_PATHS = ["/login-page", "/auth", "/public"]

export default function HideSidebar() {
  const pathname = usePathname() ?? ""
  if (HIDE_PATHS.some(p => pathname.startsWith(p))) return null
  return <AppSidebar />
}
