"use client";

import { useNoCandidateDispatch } from "@/hooks/use-no-candidate-dispatch";
import { X, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";

export function NoCandidatePopup({
  neighbourhoodId,
}: {
  neighbourhoodId: string | null;
}) {
  const { notification, dismiss } = useNoCandidateDispatch(neighbourhoodId);

  if (!notification) return null;

  return (
    <div className="fixed bottom-4 right-4 z-1200 w-[320px] max-w-[calc(100vw-2rem)] overflow-hidden rounded-xl border-2 border-brand-caution bg-brand-depth shadow-lg">
      <div className="p-4">
        <div className="mb-3 flex items-start justify-between gap-3">
          <span className="inline-flex items-center gap-1 rounded-full bg-brand-caution/15 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-brand-caution">
            <ShieldAlert className="h-3 w-3" />
            Dispatch update
          </span>

          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-brand-ash hover:text-brand-frost"
            onClick={dismiss}
            aria-label="Dismiss dispatch update"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <p className="text-sm font-semibold text-brand-frost">
          No officer was available
        </p>
        <p className="mt-1 text-xs text-brand-ash">
          Could not find an available officer to dispatch for alert{" "}
          <span className="font-mono">{notification.alertId}</span>.
        </p>
      </div>
    </div>
  );
}
