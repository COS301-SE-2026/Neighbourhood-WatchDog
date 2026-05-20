"use client"

import { usePathname } from "next/navigation"
import { AppSidebar } from "@/components/app-sidebar"

const HIDE_PATHS = ["/login-page", "/auth", "/public"]

export default function HideSidebar() {
  const pathname = usePathname() ?? ""
  if (HIDE_PATHS.some(p => pathname.startsWith(p))) { //Check if the page is allowed
    return null//not allowed, no sidebar for you nawty boy
  }else{
    return <AppSidebar /> //if allowded give sidebar
  }
  
}
// 