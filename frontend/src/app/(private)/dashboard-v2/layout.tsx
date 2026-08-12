import AppDashSidebar from "@/components/AppDashSidebar";
import Navbar from "@/components/Navbar";

export default function DashboardV2Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
        <AppDashSidebar/>
        <main className="w-full">
            <Navbar/>
            <div className="px-4">{children}</div>
        </main>
    </>
  );
}