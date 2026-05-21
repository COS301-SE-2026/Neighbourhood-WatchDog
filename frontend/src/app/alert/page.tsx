"use client";

import { useCallback, useMemo, useState } from "react";
import {
  AlertCard,
  type Alert,
  type AlertSeverity,
  type AlertStatus,
  getSeverity,
} from "@/components/shared/AlertCard";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SlidersHorizontal, RefreshCw } from "lucide-react";

const now = new Date();
const minsAgo = (m: number) =>
  new Date(now.getTime() - m * 60_000).toISOString();

const MOCK_ALERTS: Alert[] = [
  {
    id: "a1b2c3d4-0001-0001-0001-000000000001",
    camera_id: "cam-f3a9b201-0001-0001-0001-000000000001",
    detection_event_id: "evt-00000001-0001-0001-0001-000000000001",
    status: "NEW",
    created_at: minsAgo(2),
    detection_type: "WEAPON_DETECTED",
    confidence_score: 0.97,
    thumbnail_url: null,
  },
  {
    id: "a1b2c3d4-0002-0002-0002-000000000002",
    camera_id: "cam-f3a9b201-0002-0002-0002-000000000002",
    detection_event_id: "evt-00000002-0002-0002-0002-000000000002",
    status: "NEW",
    created_at: minsAgo(8),
    detection_type: "LOITERING",
    confidence_score: 0.84,
    thumbnail_url: null,
  },
  {
    id: "a1b2c3d4-0003-0003-0003-000000000003",
    camera_id: "cam-f3a9b201-0003-0003-0003-000000000003",
    detection_event_id: "evt-00000003-0003-0003-0003-000000000003",
    status: "NEW",
    created_at: minsAgo(15),
    detection_type: "HUMAN_PRESENCE",
    confidence_score: 0.76,
    thumbnail_url: null,
  },
  {
    id: "a1b2c3d4-0004-0004-0004-000000000004",
    camera_id: "cam-f3a9b201-0004-0004-0004-000000000004",
    detection_event_id: "evt-00000004-0004-0004-0004-000000000004",
    status: "ACKNOWLEDGED",
    created_at: minsAgo(34),
    detection_type: "PERIMETER_SCAN",
    confidence_score: 0.91,
    thumbnail_url: null,
  },
  {
    id: "a1b2c3d4-0005-0005-0005-000000000005",
    camera_id: "cam-f3a9b201-0005-0005-0005-000000000005",
    detection_event_id: "evt-00000005-0005-0005-0005-000000000005",
    status: "ACKNOWLEDGED",
    created_at: minsAgo(55),
    detection_type: "FALL_DETECTED",
    confidence_score: 0.88,
    thumbnail_url: null,
  },
  {
    id: "a1b2c3d4-0006-0006-0006-000000000006",
    camera_id: "cam-f3a9b201-0006-0006-0006-000000000006",
    detection_event_id: "evt-00000006-0006-0006-0006-000000000006",
    status: "RESOLVED",
    created_at: minsAgo(120),
    resolved_at: minsAgo(90),
    detection_type: "HUMAN_PRESENCE",
    confidence_score: 0.62,
    thumbnail_url: null,
  },
];

const ALL_SEVERITIES: AlertSeverity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
const ALL_STATUSES: AlertStatus[] = ["NEW", "ACKNOWLEDGED", "RESOLVED"];

const SEVERITY_LABELS: Record<AlertSeverity, string> = {
  CRITICAL: "Critical",
  HIGH: "High",
  MEDIUM: "Medium",
  LOW: "Low",
};

const STATUS_LABELS: Record<AlertStatus, string> = {
  NEW: "New",
  ACKNOWLEDGED: "Acknowledged",
  RESOLVED: "Resolved",
};

function EmptyState() {
  return (
    <div
      className="flex flex-col items-center justify-center py-20 text-center"
      role="status"
      aria-live="polite"
    >
      {/*
        On a light background, use --color-body (muted navy-grey) for de-emphasised text.
        --color-mist would be near-invisible on white; --color-body gives enough contrast.
      */}
      <p
        className="text-[15px] font-semibold"
        style={{ color: "var(--color-body)" }}
      >
        No alerts
      </p>
    </div>
  );
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>(MOCK_ALERTS);
  const [refreshKey, setRefreshKey] = useState(0);
  const [selectedSeverities, setSelectedSeverities] = useState<
    Set<AlertSeverity>
  >(new Set(ALL_SEVERITIES));
  const [selectedStatuses, setSelectedStatuses] = useState<Set<AlertStatus>>(
    new Set(["NEW", "ACKNOWLEDGED"]),
  );

  const handleAcknowledge = useCallback(async (id: string) => {
    setAlerts((prev) =>
      prev.map((a) =>
        a.id === id ? { ...a, status: "ACKNOWLEDGED" as AlertStatus } : a,
      ),
    );
  }, []);

  function handleRefresh() {
    setAlerts(MOCK_ALERTS);
    setRefreshKey((k) => k + 1);
  }

  const filtered = useMemo(
    () =>
      alerts.filter((a) => {
        const sev = getSeverity(a.detection_type);
        return (
          selectedSeverities.has(sev) &&
          selectedStatuses.has(a.status as AlertStatus)
        );
      }),
    [alerts, selectedSeverities, selectedStatuses],
  );

  const hasActiveFilters =
    selectedSeverities.size < ALL_SEVERITIES.length ||
    !selectedStatuses.has("NEW") ||
    !selectedStatuses.has("ACKNOWLEDGED") ||
    selectedStatuses.has("RESOLVED");

  const newCount = alerts.filter((a) => a.status === "NEW").length;
  const criticalCount = alerts.filter(
    (a) => getSeverity(a.detection_type) === "CRITICAL" && a.status === "NEW",
  ).length;

  return (
    <TooltipProvider>
      {/*
        Page surface: --color-fog (#F4F6FA) — the spec's light alternate surface.
        This is the dominant (60%) background on light-mode pages.
        font-sans resolves to var(--font-sans) via global.css @theme inline.
      */}
      <div
        className="w-full flex flex-col items-center px-8 py-10 min-h-full font-sans"
        style={{ backgroundColor: "var(--color-fog)" }}
      >
        <div className="w-full max-w-2xl">
          <header className="mb-6 text-center">
            {/*
              heading-1: 32px / Bold 700.
              --color-navy on --color-fog: ≥ 8:1 contrast (same ratio as white-on-navy).
            */}
            <h1
              className="text-[32px] font-bold leading-10"
              style={{ color: "var(--color-navy)" }}
            >
              Alerts
            </h1>

            {(newCount > 0 || criticalCount > 0) && (
              <div
                className="flex gap-2 mt-3 flex-wrap justify-center"
                aria-live="polite"
              >
                {newCount > 0 && (
                  /*
                    "New" informational badge: --color-blue tint bg, --color-blue text.
                    --color-blue on white-ish fog meets ≥ 4.5:1 for small text.
                  */
                  <span
                    className="inline-flex items-center gap-1 text-xs font-semibold rounded-full px-3 py-1"
                    style={{
                      backgroundColor: "color-mix(in srgb, var(--color-blue) 12%, transparent)",
                      border: "1px solid color-mix(in srgb, var(--color-blue) 25%, transparent)",
                      color: "var(--color-blue)",
                    }}
                  >
                    {newCount} new
                  </span>
                )}
                {criticalCount > 0 && (
                  /*
                    Critical badge: --color-threat tint bg, --color-threat text.
                    Solid threat red on light bg comfortably exceeds 4.5:1.
                  */
                  <span
                    className="inline-flex items-center gap-1 text-xs font-semibold rounded-full px-3 py-1"
                    style={{
                      backgroundColor: "color-mix(in srgb, var(--color-threat) 12%, transparent)",
                      border: "1px solid color-mix(in srgb, var(--color-threat) 25%, transparent)",
                      color: "var(--color-threat)",
                    }}
                  >
                    {criticalCount} critical
                  </span>
                )}
              </div>
            )}
          </header>

          {/*
            Card: white surface (--color-white) so it lifts off the fog background.
            Border: --color-mist (#D0D7E8) — the spec's border/divider token.
            shadow-sm adds subtle lift per the elevation spec.
          */}
          <Card
            className="rounded-2xl"
            style={{
              backgroundColor: "var(--color-white)",
              borderColor: "var(--color-mist)",
              boxShadow: "var(--shadow-sm)",
            }}
          >
            {/* Toolbar row */}
            <div
              className="flex items-center justify-between gap-3 px-5 py-4 rounded-t-2xl"
              style={{ borderBottom: "1px solid var(--color-mist)" }}
            >
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs font-medium transition-colors"
                    style={{
                      /*
                        Default: --color-mist border, --color-body text (readable on white).
                        Active: --color-blue border + text to signal filter is on.
                      */
                      borderColor: hasActiveFilters
                        ? "var(--color-blue)"
                        : "var(--color-mist)",
                      backgroundColor: "transparent",
                      color: hasActiveFilters
                        ? "var(--color-blue)"
                        : "var(--color-body)",
                    }}
                    aria-label="Open filter options"
                  >
                    <SlidersHorizontal className="h-3.5 w-3.5 mr-1.5" />
                    Filter
                    {hasActiveFilters && (
                      /*
                        Active-filter pip: --color-blue fill, white label.
                        White on --color-blue ≥ 4.5:1 per spec contrast table.
                      */
                      <span
                        className="ml-1.5 flex h-4 w-4 items-center justify-center rounded-full text-[9px] font-bold"
                        style={{
                          backgroundColor: "var(--color-blue)",
                          color: "var(--color-white)",
                        }}
                      >
                        !
                      </span>
                    )}
                  </Button>
                </DropdownMenuTrigger>

                {/*
                  Dropdown: white bg, mist border, ink text.
                  The dropdown sits above the light page so it stays white (not navy).
                */}
                <DropdownMenuContent
                  align="start"
                  className="w-52"
                  style={{
                    backgroundColor: "var(--color-white)",
                    borderColor: "var(--color-mist)",
                    color: "var(--color-ink)",
                  }}
                >
                  {/* Section label: caption-weight, --color-body for subdued tone */}
                  <DropdownMenuLabel
                    className="text-[10px] uppercase tracking-wider"
                    style={{ color: "var(--color-body)" }}
                  >
                    Severity
                  </DropdownMenuLabel>
                  {ALL_SEVERITIES.map((sev) => (
                    <DropdownMenuCheckboxItem
                      key={sev}
                      className="text-sm cursor-pointer"
                      style={{ color: "var(--color-ink)" }}
                      checked={selectedSeverities.has(sev)}
                      onCheckedChange={(checked) => {
                        setSelectedSeverities((prev) => {
                          const next = new Set(prev);
                          checked ? next.add(sev) : next.delete(sev);
                          return next;
                        });
                      }}
                    >
                      {SEVERITY_LABELS[sev]}
                    </DropdownMenuCheckboxItem>
                  ))}

                  <DropdownMenuSeparator
                    style={{ backgroundColor: "var(--color-mist)" }}
                  />

                  <DropdownMenuLabel
                    className="text-[10px] uppercase tracking-wider"
                    style={{ color: "var(--color-body)" }}
                  >
                    Status
                  </DropdownMenuLabel>
                  {ALL_STATUSES.map((st) => (
                    <DropdownMenuCheckboxItem
                      key={st}
                      className="text-sm cursor-pointer"
                      style={{ color: "var(--color-ink)" }}
                      checked={selectedStatuses.has(st)}
                      onCheckedChange={(checked) => {
                        setSelectedStatuses((prev) => {
                          const next = new Set(prev);
                          checked ? next.add(st) : next.delete(st);
                          return next;
                        });
                      }}
                    >
                      {STATUS_LABELS[st]}
                    </DropdownMenuCheckboxItem>
                  ))}

                  {hasActiveFilters && (
                    <>
                      <DropdownMenuSeparator
                        style={{ backgroundColor: "var(--color-mist)" }}
                      />
                      {/* Ghost: --color-blue text, no border — readable on white */}
                      <button
                        onClick={() => {
                          setSelectedSeverities(new Set(ALL_SEVERITIES));
                          setSelectedStatuses(new Set(["NEW", "ACKNOWLEDGED"]));
                        }}
                        className="w-full text-left px-2 py-1.5 text-xs transition-colors"
                        style={{ color: "var(--color-blue)" }}
                        onMouseEnter={(e) =>
                          (e.currentTarget.style.color = "var(--color-navy)")
                        }
                        onMouseLeave={(e) =>
                          (e.currentTarget.style.color = "var(--color-blue)")
                        }
                      >
                        Clear all filters
                      </button>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>

              {/*
                Ghost refresh button: --color-blue text on white card.
                Hover darkens to --color-navy, staying within the brand palette.
              */}
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRefresh}
                className="text-xs transition-colors"
                style={{ color: "var(--color-blue)" }}
                aria-label="Refresh alerts"
              >
                <RefreshCw key={refreshKey} className="h-3.5 w-3.5 mr-1.5" />
                Refresh
              </Button>
            </div>

            <section
              aria-label="Alert list"
              aria-live="polite"
              className="p-4 rounded-b-2xl"
            >
              {filtered.length === 0 ? (
                <EmptyState />
              ) : (
                <div className="space-y-3">
                  {filtered.map((alert) => (
                    <AlertCard
                      key={alert.id}
                      alert={alert}
                      onAcknowledge={handleAcknowledge}
                    />
                  ))}
                </div>
              )}
            </section>
          </Card>
        </div>
      </div>
    </TooltipProvider>
  );
}