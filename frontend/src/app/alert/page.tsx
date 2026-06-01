import { Suspense } from "react";
import AlertsPage from "./AlertsPage"; // move your current component here
import { RefreshCw } from "lucide-react";

export default function AlertPage() {
  return (
    <Suspense
      fallback={
        <div className="w-full min-h-full flex items-center justify-center bg-[#1D2A5E]">
          <RefreshCw className="h-4 w-4 animate-spin text-[#5B8DEF]" />
        </div>
      }
    >
      <AlertsPage />
    </Suspense>
  );
}