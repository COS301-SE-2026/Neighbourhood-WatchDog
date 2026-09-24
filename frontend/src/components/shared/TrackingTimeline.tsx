"use client";

import { useEffect, useState } from "react";
import { Activity, RefreshCw } from "lucide-react";
import { Card } from "@/components/ui/card";
import {
  ApiError,
  fetchTrackingTimeline,
  type TrackingTimelineData,
} from "@/lib/api/alert";
import { AlertFootagePlayer } from "@/components/shared/AlertFootagePlayer";

interface TrackingTimelineProps {
  readonly alertId: string;
  readonly alertStatus: string;
  readonly enabled: boolean;
  readonly refreshKey?: number;
}

function formatDateTime(value: string): string {
  try {
    return new Intl.DateTimeFormat("en-ZA", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

export function TrackingTimeline({
  alertId,
  alertStatus,
  enabled,
  refreshKey = 0,
}: TrackingTimelineProps) {
  const [timeline, setTimeline] = useState<TrackingTimelineData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled) return;

    const controller = new AbortController();

    async function loadTimeline() {
        setLoading(true);
        setError(null);

        try {
        const data = await fetchTrackingTimeline(
            alertId,
            controller.signal,
        );

        if (!controller.signal.aborted) {
            setTimeline(data);
        }
        } catch (reason: unknown) {
        if (
            reason instanceof DOMException &&
            reason.name === "AbortError"
        ) {
            return;
        }

        if (reason instanceof ApiError && reason.statusCode === 404) {
            setTimeline(null);
            setError("No tracking timeline is available for this alert.");
            return;
        }

        setError(
            reason instanceof Error
            ? reason.message
            : "Failed to load the tracking timeline.",
        );
        } finally {
        if (!controller.signal.aborted) {
            setLoading(false);
        }
        }
    }

    void loadTimeline();

    return () => controller.abort();
    }, [alertId, enabled, refreshKey]);

  return (
    <Card className="border-border bg-brand-depth p-4">
      <div className="mb-4 flex items-center gap-2">
        <Activity className="h-4 w-4 text-brand-green" />
        <div>
          <h3 className="text-sm font-semibold text-brand-frost">
            Tracking timeline
          </h3>
          <p className="text-xs text-brand-ash">
            Cross-camera sightings for this incident
          </p>
        </div>
      </div>

      {loading && (
        <div className="flex items-center gap-2 py-4 text-xs text-brand-ash">
          <RefreshCw className="h-4 w-4 animate-spin text-brand-green" />
          Loading tracking timeline…
        </div>
      )}

      {!loading && error && (
        <output className="block rounded-md border border-brand-caution/30 bg-brand-caution/10 px-3 py-2 text-xs text-brand-caution">
          {error}
        </output>
      )}

      {!loading && !error && timeline && (
        <>
          <div className="mb-4 grid gap-2 text-xs sm:grid-cols-2">
            <div>
              <span className="text-brand-ash">Tracking subject</span>
              <p className="mt-1 break-all font-mono text-brand-frost">
                {timeline.tracking_subject_id}
              </p>
            </div>

            <div>
              <span className="text-brand-ash">Sequence status</span>
              <p className="mt-1 text-brand-frost">
                {alertStatus === "NEW"
                  ? "Active"
                  : "Terminated after acknowledgement"}
              </p>
            </div>
          </div>

          {timeline.sightings.length === 0 ? (
            <p className="text-xs text-brand-ash">
              No sightings have been recorded yet.
            </p>
          ) : (
            <ol className="space-y-3">
              {timeline.sightings.map((sighting) => (
                <li
                  key={sighting.id}
                  className="relative border-l border-brand-green/40 pl-4"
                >
                  <span className="absolute -left-1.5 top-1 h-3 w-3 rounded-full border-2 border-brand-green bg-brand-depth" />

                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm font-medium text-brand-frost">
                      {sighting.camera_name}
                    </p>
                    <span className="rounded-full bg-brand-green/10 px-2 py-0.5 text-xs text-brand-green">
                      Sequence {sighting.sequence_no}
                    </span>
                  </div>

                  <p className="mt-1 text-xs text-brand-ash">
                    {sighting.camera_location}
                  </p>

                  <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-brand-ash/80">
                    <span>{formatDateTime(sighting.observed_at)}</span>
                    <span>Local track: {sighting.local_track_id}</span>
                    {sighting.match_confidence !== null && (
                      <span>
                        Match:{" "}
                        {(sighting.match_confidence * 100).toFixed(1)}%
                      </span>
                    )}
                  </div>

                  <div className="mt-3">
                    <AlertFootagePlayer
                      alertId={sighting.id}
                      timestamp={sighting.observed_at}
                      clipKind="tracking-sighting"
                    />
                  </div>
                </li>
              ))}
            </ol>
          )}
        </>
      )}
    </Card>
  );
}
