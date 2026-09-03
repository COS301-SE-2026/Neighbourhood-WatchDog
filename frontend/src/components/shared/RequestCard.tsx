"use client";

import { useState, type ReactNode } from "react";
import { Check, Clock, Loader2, User, X} from "lucide-react";

export type JoinRequestStatus = "PENDING" | "APPROVED" | "DENIED";

export interface JoinRequest {
  id: string;
  neighbourhood_id: string;
  user_id: string;
  user_name: string;
  status: JoinRequestStatus;
  created_at: string;
  resolved_at?: string | null;
}

export function joinRequestInitials(name: string): string {
return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase();
}

export function timeAgo(iso: string): string {
    const difference = Date.now() - new Date(iso).getTime();
    const seconds = Math.floor(difference / 1000);

    if (seconds < 60) return `${seconds}s ago`;

    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;

    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;

    return new Intl.DateTimeFormat("en-ZA", {
        dateStyle: "medium",
    }).format(new Date(iso));
}

const STATUS_CONFIG: Record<
  JoinRequestStatus,
  { label: string; className: string; icon: ReactNode }
> = {
  PENDING: {
    label: "Pending",
    className: "text-brand-caution",
    icon: <Clock className="size-3.5" />,
  },
  APPROVED: {
    label: "Approved",
    className: "text-brand-green",
    icon: <Check className="size-3.5" />,
  },
  DENIED: {
    label: "Denied",
    className: "text-brand-threat",
    icon: <X className="size-3.5" />,
  },
};

export interface RequestCardProps {
  request: JoinRequest;
  onApprove: (id: string) => Promise<void>;
  onDeny: (id: string) => Promise<void>;
}

export function RequestCard({ request, onApprove, onDeny }: RequestCardProps) {
  const [isApproving, setIsApproving] = useState(false);
  const [isDenying, setIsDenying] = useState(false);

  const isPending = request.status === "PENDING";
  const isLoading = isApproving || isDenying;
  const status = STATUS_CONFIG[request.status];

  async function handleApprove() {
      setIsApproving(true);

      try {
          await onApprove(request.id);
      } finally {
          setIsApproving(false);
      }
  }

  async function handleDeny() {
      setIsDenying(true);

      try {
          await onDeny(request.id);
      } finally {
          setIsDenying(false);
      }
  }

  return (
    <article
        className={[
            "flex flex-col gap-4 border border-border bg-brand-abyss px-4 py-4",
            "sm:flex-row sm:items-center sm:justify-between",
            isPending
                ? "transition-colors hover:border-brand-gunmetal/30"
                : "opacity-65",
        ].join(" ")}
        aria-label={`Join request from ${request.user_name}`}
    >
        <div className="flex min-w-0 items-center gap-3">
            <div className="flex size-9 shrink-0 items-center justify-center rounded-full border border-border bg-brand-slate text-xs font-medium text-brand-ash">
                {request.user_name ? (
                    joinRequestInitials(request.user_name)
                ) : (
                    <User className="size-4" />
                )}
            </div>

            <div className="min-w-0">
                <p className="truncate text-sm font-medium text-brand-frost">
                    {request.user_name || "Unknown resident"}
                </p>

                  <p className="mt-1 flex items-center gap-1.5 text-xs text-brand-ash">
                      <Clock className="size-3" />
                      Requested {timeAgo(request.created_at)}
                  </p>
              </div>
          </div>

          <div className="flex items-center justify-between gap-4 sm:justify-end">
              <span
                  className={`inline-flex items-center gap-1.5 text-xs font-medium ${status.className}`}
                  aria-label={`Status: ${status.label}`}
              >
                  {status.icon}
                  {status.label}
              </span>

              {isPending && (
                  <div className="flex items-center gap-2">
                      <button
                          type="button"
                          disabled={isLoading}
                          onClick={handleDeny}
                          className="inline-flex h-8 items-center justify-center gap-1.5 rounded-md border border-border px-3 text-xs font-medium text-brand-ash transition-colors hover:border-brand-threat/30 hover:bg-brand-threat/10 hover:text-brand-threat disabled:cursor-not-allowed disabled:opacity-50"
                      >
                          {isDenying ? (
                              <Loader2 className="size-3.5 animate-spin" />
                          ) : (
                              <>
                                  <X className="size-3.5" />
                                  Deny
                              </>
                          )}
                      </button>

                      <button
                          type="button"
                          disabled={isLoading}
                          onClick={handleApprove}
                          className="inline-flex h-8 items-center justify-center gap-1.5 rounded-md bg-brand-green px-3 text-xs font-medium text-brand-void transition-colors hover:bg-brand-green disabled:cursor-not-allowed disabled:bg-brand-green/30 disabled:text-brand-void/50"
                      >
                          {isApproving ? (
                              <Loader2 className="size-3.5 animate-spin" />
                          ) : (
                              <>
                                  <Check className="size-3.5" />
                                  Approve
                              </>
                          )}
                      </button>
                  </div>
              )}
          </div>
      </article>
  );
}