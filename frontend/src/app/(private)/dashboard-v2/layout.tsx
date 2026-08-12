import AppDashSidebar from "@/components/AppDashSidebar";
import Navbar from "@/components/Navbar";
import { SidebarProvider } from "@/components/ui/sidebar";

export default function DashboardV2Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
        <SidebarProvider>
          <AppDashSidebar/>
          <main className="w-full">
              <Navbar/>
              <div className="px-4">{children}</div>
          </main>
        </SidebarProvider>
    </>
  );
}