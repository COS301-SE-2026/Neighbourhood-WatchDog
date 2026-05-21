"use client";

import { useState, type ReactNode } from "react";
import Image from "next/image";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import {
  AlertTriangle,
  ShieldAlert,
  Info,
  CheckCircle2,
  Clock,
  Camera,
  Activity,
  CheckCheck,
  ChevronRight,
  Loader2,
} from "lucide-react";

export type AlertSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
export type AlertStatus = "NEW" | "ACKNOWLEDGED" | "RESOLVED";

export interface Alert {
  id: string;
  camera_id: string;
  detection_event_id: string;
  status: AlertStatus;
  resolved_by?: string | null;
  resolved_at?: string | null;
  created_at: string;
  detection_type?: string | null;
  confidence_score?: number | null;
  thumbnail_url?: string | null;
}

export function getSeverity(detection_type?: string | null): AlertSeverity {
  switch (detection_type) {
    case "WEAPON_DETECTED":
    case "FALL_DETECTED":
      return "CRITICAL";
    case "LOITERING":
    case "PERIMETER_SCAN":
      return "HIGH";
    case "HUMAN_PRESENCE":
      return "MEDIUM";
    default:
      return "LOW";
  }
}

const SEVERITY_CONFIG: Record<
  AlertSeverity,
  { bg: string; label: string; icon: ReactNode }
> = {
  CRITICAL: {
    bg: "bg-[#DC2626] text-white",
    label: "Critical",
    icon: <ShieldAlert className="h-3 w-3" />,
  },
  HIGH: {
    bg: "bg-[#D97706] text-white",
    label: "High",
    icon: <AlertTriangle className="h-3 w-3" />,
  },
  MEDIUM: {
    bg: "bg-[#0284C7] text-white",
    label: "Medium",
    icon: <Info className="h-3 w-3" />,
  },
  LOW: {
    bg: "bg-[#16A34A] text-white",
    label: "Low",
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
};

const STATUS_CONFIG: Record<
  AlertStatus,
  { bg: string; textColor: string; label: string; icon: ReactNode }
> = {
  NEW: {
    bg: "bg-[#3B5EDE]/20 border border-[#3B5EDE]/40",
    textColor: "text-[#5B8DEF]",
    label: "New",
    icon: <Activity className="h-3 w-3" />,
  },
  ACKNOWLEDGED: {
    bg: "bg-[#D0D7E8]/20 border border-[#D0D7E8]/40",
    textColor: "text-[#D0D7E8]",
    label: "Acknowledged",
    icon: <CheckCheck className="h-3 w-3" />,
  },
  RESOLVED: {
    bg: "bg-[#16A34A]/20 border border-[#16A34A]/40",
    textColor: "text-[#16A34A]",
    label: "Resolved",
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
};

export function SeverityBadge({ severity }: { severity: AlertSeverity }) {
  const config = SEVERITY_CONFIG[severity];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${config.bg}`}
      aria-label={`Severity: ${config.label}`}
    >
      {config.icon}
      {config.label}
    </span>
  );
}

export function StatusBadge({ status }: { status: AlertStatus }) {
  const config = STATUS_CONFIG[status];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${config.bg} ${config.textColor}`}
      aria-label={`Status: ${config.label}`}
    >
      {config.icon}
      {config.label}
    </span>
  );
}

export function detectionLabel(type?: string | null): string {
  const map: Record<string, string> = {
    HUMAN_PRESENCE: "Person detected",
    LOITERING: "Loitering detected",
    PERIMETER_SCAN: "Perimeter scanning",
    WEAPON_DETECTED: "Weapon detected",
    FALL_DETECTED: "Fall detected",
  };
  return type ? (map[type] ?? type) : "Unknown event";
}

export function formatDateTime(iso: string): string {
  try {
    return new Intl.DateTimeFormat("en-ZA", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const secs = Math.floor(diff / 1000);
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return formatDateTime(iso);
}

interface AlertDetailSheetProps {
  alert: Alert;
  open: boolean;
  onClose: () => void;
  onAcknowledge: (id: string) => Promise<void>;
  acknowledging: boolean;
}

function AlertDetailSheet({
  alert,
  open,
  onClose,
  onAcknowledge,
  acknowledging,
}: AlertDetailSheetProps) {
  const severity = getSeverity(alert.detection_type);
  const isNew = alert.status === "NEW";

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        side="right"
        className="w-full max-w-md border-l border-[#2C3E6B] bg-[#1D2A5E] text-white"
        style={{ boxShadow: "var(--shadow-lg)" }}
      >
        <SheetHeader className="mb-6">
          <div className="flex items-center gap-2 mb-1">
            <SeverityBadge severity={severity} />
            <StatusBadge status={alert.status} />
          </div>
          <SheetTitle className="text-white text-[20px] font-semibold leading-7">
            {detectionLabel(alert.detection_type)}
          </SheetTitle>
          <SheetDescription className="text-[#D0D7E8] text-sm">
            Full alert details
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-4">
          {alert.thumbnail_url ? (
            <div className="relative rounded-lg overflow-hidden border border-[#2C3E6B]">
              <Image
                src={alert.thumbnail_url}
                alt="Detection thumbnail"
                width={800}
                height={450}
                sizes="(max-width: 768px) 100vw, 400px"
                className="h-auto w-full object-cover"
              />
            </div>
          ) : (
            <div className="rounded-lg border border-[#2C3E6B] bg-[#2C3E6B]/40 h-40 flex items-center justify-center gap-2">
              <Camera className="h-8 w-8 text-[#5B8DEF] opacity-50" />
              <span className="text-sm text-[#D0D7E8]/60">No thumbnail</span>
            </div>
          )}

          <Separator className="bg-[#2C3E6B]" />

          <div className="space-y-3">
            <MetaRow label="Alert ID" value={alert.id} mono />
            <MetaRow label="Camera ID" value={alert.camera_id} mono />
            <MetaRow
              label="Detection event"
              value={alert.detection_event_id}
              mono
            />
            <MetaRow
              label="Detection type"
              value={detectionLabel(alert.detection_type)}
            />
            {alert.confidence_score != null && (
              <MetaRow
                label="Confidence score"
                value={`${(alert.confidence_score * 100).toFixed(1)}%`}
              />
            )}
            <MetaRow
              label="Detected at"
              value={formatDateTime(alert.created_at)}
              mono
            />
            {alert.resolved_at && (
              <MetaRow
                label="Resolved at"
                value={formatDateTime(alert.resolved_at)}
                mono
              />
            )}
          </div>

          <Separator className="bg-[#2C3E6B]" />

          {isNew && (
            <Button
              className="w-full bg-[#3B5EDE] hover:bg-[#5B8DEF] text-white font-medium transition-colors duration-200 focus-visible:ring-2 focus-visible:ring-[#3B5EDE] focus-visible:ring-offset-2 focus-visible:ring-offset-[#1D2A5E]"
              onClick={() => onAcknowledge(alert.id)}
              disabled={acknowledging}
              aria-label="Acknowledge this alert"
            >
              {acknowledging ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Acknowledging…
                </>
              ) : (
                <>
                  <CheckCheck className="mr-2 h-4 w-4" />
                  Acknowledge alert
                </>
              )}
            </Button>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

function MetaRow({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-xs font-medium text-[#D0D7E8]/70 shrink-0">
        {label}
      </span>
      <span
        className={`text-xs text-white text-right break-all ${mono ? "font-mono" : ""}`}
      >
        {value}
      </span>
    </div>
  );
}

export interface AlertCardProps {
  alert: Alert;
  onAcknowledge: (id: string) => Promise<void>;
}

export function AlertCard({ alert, onAcknowledge }: AlertCardProps) {
  const [detailOpen, setDetailOpen] = useState(false);
  const [acknowledging, setAcknowledging] = useState(false);

  const severity = getSeverity(alert.detection_type);
  const isNew = alert.status === "NEW";
  const isCritical = severity === "CRITICAL";

  async function handleAcknowledge(id: string) {
    setAcknowledging(true);
    try {
      await onAcknowledge(id);
    } finally {
      setAcknowledging(false);
      setDetailOpen(false);
    }
  }

  return (
    <>
      <Card
        className={[
          "relative flex flex-col sm:flex-row sm:items-center gap-4 p-4 rounded-xl border transition-all duration-200",
          "bg-[#2C3E6B] border-[#2C3E6B]",
          isNew
            ? "hover:border-[#3B5EDE]/60 hover:shadow-md"
            : "opacity-80 hover:opacity-100",
          isCritical && isNew
            ? "border-[#DC2626]/40 shadow-[0_0_0_1px_rgba(220,38,38,0.20)]"
            : "",
        ]
          .filter(Boolean)
          .join(" ")}
        role="article"
        aria-label={`Alert: ${detectionLabel(alert.detection_type)}`}
      >
        {/* Content */}
        <div className="flex-1 pl-3 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <SeverityBadge severity={severity} />
            <StatusBadge status={alert.status} />
          </div>
          <p className="text-[15px] font-semibold text-white leading-snug truncate">
            {detectionLabel(alert.detection_type)}
          </p>
          <div className="flex flex-wrap items-center gap-3 mt-1">
            <span className="flex items-center gap-1 text-[11px] text-[#D0D7E8]/70 font-mono">
              <Camera className="h-3 w-3" />
              {alert.camera_id.slice(0, 8)}…
            </span>
            {alert.confidence_score != null && (
              <span className="text-[11px] text-[#D0D7E8]/70 font-mono">
                {(alert.confidence_score * 100).toFixed(0)}% confidence
              </span>
            )}
            <span className="flex items-center gap-1 text-[11px] text-[#D0D7E8]/60 font-mono">
              <Clock className="h-3 w-3" />
              {timeAgo(alert.created_at)}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 shrink-0">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="text-[#5B8DEF] hover:text-white hover:bg-[#3B5EDE]/20 text-xs font-medium transition-colors duration-100"
                onClick={() => setDetailOpen(true)}
                aria-label="View alert details"
              >
                Details
                <ChevronRight className="h-3.5 w-3.5 ml-1" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="top">View full alert details</TooltipContent>
          </Tooltip>

          {isNew && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  size="sm"
                  className="bg-[#3B5EDE] hover:bg-[#5B8DEF] text-white text-xs font-semibold transition-colors duration-100 focus-visible:ring-2 focus-visible:ring-[#3B5EDE] focus-visible:ring-offset-2 focus-visible:ring-offset-[#2C3E6B]"
                  onClick={() => handleAcknowledge(alert.id)}
                  disabled={acknowledging}
                  aria-label="Acknowledge alert"
                >
                  {acknowledging ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <>
                      <CheckCheck className="h-3.5 w-3.5 mr-1" />
                      Acknowledge
                    </>
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent side="top">
                Mark alert as acknowledged
              </TooltipContent>
            </Tooltip>
          )}
        </div>
      </Card>

      <AlertDetailSheet
        alert={alert}
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        onAcknowledge={handleAcknowledge}
        acknowledging={acknowledging}
      />
    </>
  );
}
