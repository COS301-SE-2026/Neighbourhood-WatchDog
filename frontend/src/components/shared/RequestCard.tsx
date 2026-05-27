"use client";

import { useState, type ReactNode } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCheck, XCircle, Clock, Loader2, User } from "lucide-react";

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
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
}

export function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const secs = Math.floor(diff / 1000);
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return new Intl.DateTimeFormat("en-ZA", { dateStyle: "medium" }).format(
    new Date(iso),
  );
}

const STATUS_CONFIG: Record<
  JoinRequestStatus,
  { badge: string; label: string; icon: ReactNode }
> = {
  PENDING: {
    badge: "bg-[#3B5EDE]/20 border border-[#3B5EDE]/40 text-[#5B8DEF]",
    label: "Pending",
    icon: <Clock className="h-2.5 w-2.5" />,
  },
  APPROVED: {
    badge: "bg-[#16A34A]/15 border border-[#16A34A]/30 text-[#16A34A]",
    label: "Approved",
    icon: <CheckCheck className="h-2.5 w-2.5" />,
  },
  DENIED: {
    badge: "bg-[#DC2626]/12 border border-[#DC2626]/25 text-[#DC2626]",
    label: "Denied",
    icon: <XCircle className="h-2.5 w-2.5" />,
  },
};

const AVATAR_CONFIG: Record<
  JoinRequestStatus,
  { bg: string; border: string; text: string }
> = {
  PENDING: {
    bg: "bg-[#3B5EDE]/20",
    border: "border-[#3B5EDE]/30",
    text: "text-[#5B8DEF]",
  },
  APPROVED: {
    bg: "bg-[#16A34A]/15",
    border: "border-[#16A34A]/25",
    text: "text-[#16A34A]",
  },
  DENIED: {
    bg: "bg-[#DC2626]/12",
    border: "border-[#DC2626]/20",
    text: "text-[#DC2626]",
  },
};

export interface RequestCardProps {
  request: JoinRequest;
  onApprove: (id: string) => Promise<void>;
  onDeny: (id: string) => Promise<void>;
}

export function RequestCard({ request, onApprove, onDeny }: RequestCardProps) {
  const [approvingId, setApprovingId] = useState(false);
  const [denyingId, setDenyingId] = useState(false);

  const isPending = request.status === "PENDING";
  const isLoading = approvingId || denyingId;

  const statusCfg = STATUS_CONFIG[request.status];
  const avatarCfg = AVATAR_CONFIG[request.status];

  async function handleApprove() {
    setApprovingId(true);
    try {
      await onApprove(request.id);
    } finally {
      setApprovingId(false);
    }
  }

  async function handleDeny() {
    setDenyingId(true);
    try {
      await onDeny(request.id);
    } finally {
      setDenyingId(false);
    }
  }

  return (
    <Card
      className={[
        "flex flex-col items-center gap-3 px-4 py-4 rounded-xl border transition-all duration-150",
        "bg-[#2C3E6B] border-[#2C3E6B]",
        isPending ? "hover:border-[#3B5EDE]/50" : "opacity-70 hover:opacity-90",
      ]
        .filter(Boolean)
        .join(" ")}
      role="article"
      aria-label={`Join request from ${request.user_name}`}
    >
      {/* Avatar */}
      <div
        className={[
          "h-10 w-10 rounded-full border flex items-center justify-center shrink-0",
          "text-[13px] font-semibold tracking-wide",
          avatarCfg.bg,
          avatarCfg.border,
          avatarCfg.text,
        ].join(" ")}
        aria-hidden="true"
      >
        {request.user_name ? (
          joinRequestInitials(request.user_name)
        ) : (
          <User className="h-4 w-4" />
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0 text-center">
        <p className="text-[14px] font-semibold text-white truncate leading-snug">
          {request.user_name}
        </p>
        <div className="flex flex-wrap items-center gap-3 mt-0.5">
          <span className="flex items-center gap-1 text-[11px] text-[#D0D7E8]/60 font-mono">
            <Clock className="h-2.5 w-2.5" />
            {timeAgo(request.created_at)}
          </span>
          <span className="text-[11px] text-[#D0D7E8]/40 font-mono truncate hidden sm:inline">
            {request.id}
          </span>
        </div>
      </div>

      {/* Status badge */}
      <span
        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-widest shrink-0 ${statusCfg.badge}`}
        aria-label={`Status: ${statusCfg.label}`}
      >
        {statusCfg.icon}
        {statusCfg.label}
      </span>

      {/* Actions (only for pending) */}
      {isPending && (
        <div className="flex items-center gap-2 shrink-0">
          <Button
            size="sm"
            disabled={isLoading}
            onClick={handleApprove}
            aria-label="Approve join request"
            className="bg-[#16A34A]/15 hover:bg-[#16A34A]/30 text-[#16A34A] border border-[#16A34A]/30 text-[11px] font-semibold transition-colors duration-100 h-7 px-3"
          >
            {approvingId ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <>
                <CheckCheck className="h-3 w-3 mr-1" />
                Approve
              </>
            )}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            disabled={isLoading}
            onClick={handleDeny}
            aria-label="Deny join request"
            className="bg-[#DC2626]/10 hover:bg-[#DC2626]/20 text-[#DC2626] border border-[#DC2626]/25 text-[11px] font-semibold transition-colors duration-100 h-7 px-3"
          >
            {denyingId ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <>
                <XCircle className="h-3 w-3 mr-1" />
                Deny
              </>
            )}
          </Button>
        </div>
      )}
    </Card>
  );
}
