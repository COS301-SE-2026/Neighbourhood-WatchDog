"use client";

import { useState, type ReactNode } from "react";
import Image from "next/image";
import dynamic from "next/dynamic";
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
  Megaphone,
} from "lucide-react";

import { AlertFootagePlayer } from "@/components/shared/AlertFootagePlayer";


type AlertLocationMapProps = {
  readonly latitude: number;
  readonly longitude: number;

};


const AlertLocationMap = dynamic<AlertLocationMapProps>(
  () =>
    import("@/components/shared/AlertLocationMap").then(
      (module) => module.AlertLocationMap
    ),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-48 items-center justify-center rounded-lg border border-border bg-brand-slate text-xs text-brand-ash/70">
        Loading map…
      </div>
    )
  }
);


export type AlertSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
export type AlertStatus = "NEW" | "ACKNOWLEDGED" | "RESOLVED";

export interface Alert {
  id: string;
  camera_id: string;
  frame_timestamp: string;
  detection_type: string;
  confidence_score: number;
  thumbnail_url?: string | null;
  clip_s3_key?: string | null;
  status: AlertStatus;
  resolved_by?: string | null;
  resolved_at?: string | null;
  created_at: string;
  property_address?: string | null;
  property_latitude?: number | null;
  property_longitude?: number | null;

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

const SEVERITY_CONFIG: Record<AlertSeverity, { bg: string; label: string; icon: ReactNode }> = {
  CRITICAL: {
    bg: "bg-brand-threat text-brand-frost",
    label: "Critical",
    icon: <ShieldAlert className="h-3 w-3" />,
  },
  HIGH: {
    bg: "bg-brand-caution text-brand-void",
    label: "High",
    icon: <AlertTriangle className="h-3 w-3" />,
  },
  MEDIUM: {
    bg: "bg-brand-pulse text-brand-frost",
    label: "Medium",
    icon: <Info className="h-3 w-3" />,
  },
  LOW: {
    bg: "bg-brand-green text-brand-void",
    label: "Low",
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
};

const STATUS_CONFIG: Record<AlertStatus, { bg: string; textColor: string; label: string; icon: ReactNode }> = {
  NEW: {
    bg: "bg-brand-pulse/15 border border-brand-pulse/40",
    textColor: "text-brand-pulse",
    label: "New",
    icon: <Activity className="h-3 w-3" />,
  },
  ACKNOWLEDGED: {
    bg: "bg-brand-slate border border-brand-gunmetal/20",
    textColor: "text-brand-ash",
    label: "Acknowledged",
    icon: <CheckCheck className="h-3 w-3" />,
  },
  RESOLVED: {
    bg: "bg-brand-green/15 border border-brand-green/40",
    textColor: "text-brand-green",
    label: "Resolved",
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
};

export function SeverityBadge({ severity }: { severity: AlertSeverity }) {
  const config = SEVERITY_CONFIG[severity];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold uppercase tracking-wide ${config.bg}`}
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
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${config.bg} ${config.textColor}`}
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
  onAcknowledge?: (id: string) => Promise<void>;
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
        className="w-full max-w-md border-l border-border bg-brand-void text-brand-frost"
      >
        <SheetHeader className="mb-6">
          <div className="flex items-center gap-2 mb-1">
            <SeverityBadge severity={severity} />
            <StatusBadge status={alert.status} />
          </div>
          <SheetTitle className="text-brand-frost text-xl font-semibold leading-7">
            {detectionLabel(alert.detection_type)}
          </SheetTitle>
          <SheetDescription className="text-brand-ash text-sm">
            Full alert details
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-4">
          {alert.thumbnail_url ? (
            <div className="relative rounded-lg overflow-hidden border border-border">
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
            <div className="rounded-lg border border-border bg-brand-slate h-40 flex items-center justify-center gap-2">
              <Camera className="h-8 w-8 text-brand-green opacity-50" />
              <span className="text-sm text-brand-ash/60">No thumbnail</span>
            </div>
          )}

          {alert.detection_type === "WEAPON_DETECTED" && (
            <AlertFootagePlayer
              alertId={alert.id}
              timestamp={alert.created_at}
            />

          )}

          <Separator className="bg-brand-slate" />

          <section aria-labelledby="alert-location-heading" className="space-y-3">
            <div>
              <h3 id="alert-location-heading" className="text-sm font-semibold text-brand-frost">
                Event location
              </h3>
              <p className="mt-1 text-xs text-brand-ash">
                Location inherited from the property connected to this camera.
              </p>
            </div>

            {alert.property_address ? (
              <p className="rounded-md border border-border bg-brand-slate px-3 py-2 text-sm text-brand-frost">
                {alert.property_address}
              </p>
            ) : (
              <p className="rounded-md border border-border bg-brand-slate px-3 py-2 text-sm text-brand-ash">
                Property address is unavailable.
              </p>
            )}

            {typeof alert.property_latitude === "number" && Number.isFinite(alert.property_latitude) && typeof alert.property_longitude === "number" && Number.isFinite(alert.property_longitude) ? (
              <AlertLocationMap
                latitude={alert.property_latitude}
                longitude={alert.property_longitude}
              />
            ) : (
              <p
                role="status"
                className="rounded-md border border-brand-caution/20 bg-brand-caution/10 px-3 py-2 text-xs text-brand-caution"
              >
                Map unavailable because this property has no saved coordinates. The property address remains available above.
              </p>
            )}
          </section>

          <Separator className="bg-brand-slate" />

          <div className="space-y-3">
            <MetaRow label="Alert ID" value={alert.id} mono />
            <MetaRow label="Camera ID" value={alert.camera_id} mono />
            <MetaRow
              label="Detection event"
              value={alert.id}
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

          <Separator className="bg-brand-slate" />

          {onAcknowledge && isNew && (
            <Button
              className="w-full bg-brand-green hover:bg-brand-green text-brand-void font-medium transition-colors duration-200 focus-visible:ring-2 focus-visible:ring-brand-green focus-visible:ring-offset-2 focus-visible:ring-offset-brand-void"
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
      <span className="text-xs font-medium text-brand-ash shrink-0">
        {label}
      </span>
      <span
        className={`text-xs text-brand-frost text-right break-all ${mono ? "font-mono" : ""}`}
      >
        {value}
      </span>
    </div>
  );
}

export interface AlertCardProps {
  readonly alert: Alert;
  readonly onAcknowledge?: (id: string) => Promise<void>;
  readonly onBroadcast?: (id: string) => Promise<void>;
  readonly broadcasting: boolean;
}

export function AlertCard({ alert, onAcknowledge, onBroadcast, broadcasting}: AlertCardProps) {
  const [detailOpen, setDetailOpen] = useState(false);
  const [acknowledging, setAcknowledging] = useState(false);

  const severity = getSeverity(alert.detection_type);
  const isNew = alert.status === "NEW";
  const isCritical = severity === "CRITICAL";

  async function handleAcknowledge(id: string) {
    if (!onAcknowledge) {
      return;
    }
    setAcknowledging(true);
    try {
      await onAcknowledge(id);
    } finally {
      setAcknowledging(false);
      setDetailOpen(false);
    }
  }

  async function handleBroadcast() {
    if (!onBroadcast) {
      return;
    }

    await onBroadcast(alert.id);
  }

  return (
    <>
      <Card
        className={[
          "relative flex flex-col sm:flex-row sm:items-center gap-4 p-4 rounded-xl border transition-all duration-200",
          "bg-brand-depth border-border",
          isNew
            ? "hover:border-brand-green/50 hover:shadow-md"
            : "opacity-80 hover:opacity-100",
          isCritical && isNew
            ? "border-brand-threat/40"
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
          <p className="text-base font-semibold text-brand-frost leading-snug truncate">
            {detectionLabel(alert.detection_type)}
          </p>
          <div className="flex flex-wrap items-center gap-3 mt-1">
            <span className="flex items-center gap-1 text-xs text-brand-ash font-mono">
              <Camera className="h-3 w-3" />
              {alert.camera_id.slice(0, 8)}…
            </span>
            {alert.confidence_score != null && (
              <span className="text-xs text-brand-ash font-mono">
                {(alert.confidence_score * 100).toFixed(0)}% confidence
              </span>
            )}
            <span className="flex items-center gap-1 text-xs text-brand-ash/70 font-mono">
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
                className="text-brand-green hover:bg-brand-slate hover:text-brand-frost text-xs font-medium transition-colors duration-100"
                onClick={() => setDetailOpen(true)}
                aria-label="View alert details"
              >
                Details
                <ChevronRight className="ml-1 h-3.5 w-3.5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="top">View full alert details</TooltipContent>
          </Tooltip>

          {onBroadcast && isNew && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  className="border-brand-threat/40 text-brand-threat hover:bg-brand-threat hover:text-brand-frost text-xs font-semibold transition-colors duration-100"
                  onClick={handleBroadcast}
                  disabled={broadcasting}
                  aria-label="Broadcast alert to the neighbourhood"
                >
                  {broadcasting ? (
                    <>
                      <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
                      Sending
                    </>
                  ) : (
                    <>
                      <Megaphone className="mr-1 h-3.5 w-3.5" />
                      Broadcast
                    </>
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent side="top">
                Notify the neighbourhood about this alert
              </TooltipContent>
            </Tooltip>
          )}

          {onAcknowledge && isNew && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  size="sm"
                  className="bg-brand-green hover:bg-brand-green text-brand-void text-xs font-semibold transition-colors duration-100 focus-visible:ring-2 focus-visible:ring-brand-green focus-visible:ring-offset-2 focus-visible:ring-offset-brand-depth"
                  onClick={() => handleAcknowledge(alert.id)}
                  disabled={acknowledging || broadcasting}
                  aria-label="Acknowledge alert"
                >
                  {acknowledging ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <>
                      <CheckCheck className="mr-1 h-3.5 w-3.5" />
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
