"use client";

import { useEffect, useState } from "react";
import { FileDown, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchSituationalBrief,
  type SituationalBriefData,
} from "@/lib/api/alert";


interface SituationalBriefProps {
  readonly alertId: string;
  readonly enabled: boolean;
  readonly refreshKey?: number;
}


function formatBriefDate(value: string): string {
  try {
    return new Intl.DateTimeFormat("en-ZA", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

export function SituationalBrief({alertId, enabled, refreshKey = 0}: SituationalBriefProps) {

  const [brief, setBrief] = useState<SituationalBriefData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const controller = new AbortController();

    async function loadBrief() {
      setLoading(true);
      setError(null);

      try {
        const result = await fetchSituationalBrief(alertId, controller.signal);

        if (!controller.signal.aborted) {
          setBrief(result);
        }
      } catch (reason: unknown) {
        if (reason instanceof DOMException && reason.name === "AbortError") {
          return;
        }

        if (reason instanceof ApiError && reason.statusCode === 404) {
          setBrief(null);
          setError("The situational brief is not available yet.");
          return;
        }

        setError(reason instanceof Error ? reason.message : "Failed to load the situational brief.");
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void loadBrief();

    return () => controller.abort();
  }, [alertId, enabled, refreshKey]);

  return (
    <section
      id={`situational-brief-${alertId}`}
      className="rounded-lg border border-brand-green/30 bg-brand-depth p-4"
      aria-labelledby={`situational-brief-heading-${alertId}`}
    >
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h3
            id={`situational-brief-heading-${alertId}`}
            className="text-sm font-semibold text-brand-frost"
          >
            Situational brief
          </h3>
          <p className="mt-1 text-xs text-brand-ash">
            Officer-only summary of the tracked subject
          </p>
        </div>

        {brief && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="gap-2"
            onClick={() => window.print()}
          >
            <FileDown className="h-4 w-4" />
            Save as PDF
          </Button>
        )}
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-xs text-brand-ash">
          <RefreshCw className="h-4 w-4 animate-spin" />
          Loading situational brief…
        </div>
      )}

      {!loading && error && (
        <p className="rounded-md border border-brand-caution/30 bg-brand-caution/10 px-3 py-2 text-xs text-brand-caution">
          {error}
        </p>
      )}

      {!loading && !error && brief && (
        <div className="space-y-4 text-xs">
          <p className="text-sm leading-6 text-brand-frost">
            {brief.summary}
          </p>

          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <span className="text-brand-ash">
                Tracking ID
              </span>
              <p className="mt-1 break-all font-mono text-brand-frost">
                {brief.tracking_subject_id}
              </p>
            </div>

            <div>
              <span className="text-brand-ash">
                Generated
              </span>
              <p className="mt-1 text-brand-frost">
                {formatBriefDate(brief.generated_at)}
              </p>
            </div>

            <div>
              <span className="text-brand-ash">
                Trigger
              </span>
              <p className="mt-1 text-brand-frost">
                {brief.trigger.replaceAll("_", " ")}
              </p>
            </div>

            <div>
              <span className="text-brand-ash">
                Last known location
              </span>
              <p className="mt-1 text-brand-frost">
                {brief.last_known_location.camera_name}
                {" — "}
                {brief.last_known_location.camera_location}
              </p>
            </div>
          </div>

          <div>
            <h4 className="mb-2 font-semibold text-brand-frost">
              Cameras visited
            </h4>

            <ul className="space-y-1 text-brand-ash">
              {brief.cameras.map((camera) => (
                <li key={camera.camera_id}>
                  {camera.camera_name}
                  {" — "}
                  {camera.camera_location}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="mb-2 font-semibold text-brand-frost">
              Associated alerts
            </h4>

            <ul className="space-y-1 text-brand-ash">
              {brief.alerts.map((alert) => (
                <li key={alert.alert_id}>
                  {alert.detection_type}
                  {" — "}
                  {formatBriefDate(alert.observed_at)}
                  {" — "}
                  {(alert.confidence_score * 100).toFixed(1)}%
                  {" confidence"}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="mb-2 font-semibold text-brand-frost">
              Sightings
            </h4>

            <ol className="space-y-1 text-brand-ash">
              {brief.sightings.map((sighting) => (
                <li key={sighting.sighting_id}>
                  #{sighting.sequence_no}
                  {" — "}
                  {sighting.camera_name}
                  {" — "}
                  {formatBriefDate(sighting.observed_at)}
                </li>
              ))}
            </ol>
          </div>
        </div>
      )}
    </section>
  );
}