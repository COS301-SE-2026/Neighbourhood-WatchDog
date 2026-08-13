import AppDashSidebar from "@/components/AppDashSidebar";
import Navbar from "@/components/Navbar";
import { SidebarProvider } from "@/components/ui/sidebar";
import { cookies } from "next/headers";

export default async function DashboardV2Layout({
  children,
}: {
  children: React.ReactNode;
}) {

  const cookieStore = await cookies()
  const defaultOpen = cookieStore.get("sidebar_state")?.value === "true"

  return (
    <>
        <SidebarProvider defaultOpen={defaultOpen}>
          <AppDashSidebar/>
          <main className="w-full bg-black">
              <Navbar/>
              <div className="px-4">{children}</div>
          </main>
        </SidebarProvider>
    </>
  );
}