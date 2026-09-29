"use client";

import { useEffect, useMemo, useState } from "react";
import { Ban, Film, Loader2, Lock, VideoOff } from "lucide-react";
import { useClip, type ClipKind } from "@/hooks/use-clip";
import { fetchTrackingTimeline, type TrackingSighting } from "@/lib/api/alert";

interface SequencedFootagePlayerProps {
  readonly alertId: string;
  readonly alertTimestamp: string;
  readonly enabled: boolean;
  readonly sightings?: TrackingSighting[];
  readonly refreshKey?: number;
}

interface PlaylistItem {
  readonly id: string;
  readonly kind: ClipKind;
  readonly label: string;
  readonly timestamp: string;
}

/**
 * Plays the origin clip and then advances through uploaded cross-camera
 * sighting clips in movement order.
 */
export function SequencedFootagePlayer({
  alertId,
  alertTimestamp,
  enabled,
  sightings: providedSightings,
  refreshKey = 0,
}: SequencedFootagePlayerProps) {
  const [sightings, setSightings] = useState<TrackingSighting[]>([]);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (!enabled) return;

    if (providedSightings) {
      setSightings(
        providedSightings.filter((sighting) => sighting.clip_s3_key),
      );
      return;
    }

    const controller = new AbortController();

    async function loadSightings() {
      try {
        const data = await fetchTrackingTimeline(alertId, controller.signal);

        if (!controller.signal.aborted) {
          setSightings(data.sightings.filter((sighting) => sighting.clip_s3_key));
        }
      } catch (reason: unknown) {
        if (reason instanceof DOMException && reason.name === "AbortError") {
          return;
        }

        // The origin clip remains available even when the tracking timeline
        // has not been created yet or cannot currently be loaded.
        if (!controller.signal.aborted) {
          setSightings([]);
        }
      }
    }

    void loadSightings();

    return () => controller.abort();
  }, [alertId, enabled, providedSightings, refreshKey]);

  useEffect(() => {
    setIndex(0);
  }, [alertId, refreshKey]);

  const playlist = useMemo<PlaylistItem[]>(() => {
    const items: PlaylistItem[] = [
      {
        id: alertId,
        kind: "alert",
        label: "Origin camera",
        timestamp: alertTimestamp,
      },
    ];

    const ordered = [...sightings].sort((left, right) => {
      const timeDifference =
        new Date(left.observed_at).getTime() -
        new Date(right.observed_at).getTime();

      if (timeDifference !== 0) return timeDifference;
      if (left.sequence_no !== right.sequence_no) {
        return left.sequence_no - right.sequence_no;
      }

      return left.id.localeCompare(right.id);
    });

    for (const sighting of ordered) {
      items.push({
        id: sighting.id,
        kind: "tracking-sighting",
        label: sighting.camera_name,
        timestamp: sighting.observed_at,
      });
    }

    return items;
  }, [alertId, alertTimestamp, sightings]);

  const current = playlist[Math.min(index, playlist.length - 1)];
  const { url, status, errorMessage } = useClip(current.id, current.kind);

  useEffect(() => {
    if (index === 0) return;

    if (
      status === "unavailable" ||
      status === "error" ||
      status === "expired" ||
      status === "forbidden"
    ) {
      const timeoutId = setTimeout(() => {
        setIndex((previous) => Math.min(previous + 1, playlist.length - 1));
      }, 1500);

      return () => clearTimeout(timeoutId);
    }
  }, [index, playlist.length, status]);

  const formattedTimestamp = (() => {
    try {
      return new Intl.DateTimeFormat("en-ZA", {
        dateStyle: "medium",
        timeStyle: "medium",
      }).format(new Date(current.timestamp));
    } catch {
      return current.timestamp;
    }
  })();

  if (status === "idle" || status === "loading" || status === "processing") {
    return (
      <div className="flex items-center gap-2 py-2 text-xs font-mono text-mist/70">
        <Loader2 className="h-3.5 w-3.5 animate-spin text-brand-pulse" />
        {status === "processing"
          ? "Footage is being prepared..."
          : "Loading continuous footage..."}
      </div>
    );
  }

  if (status === "expired") {
    return (
      <div className="flex items-center gap-2 py-2 text-xs font-mono text-mist/50 line-through">
        <VideoOff className="h-3.5 w-3.5 shrink-0" />
        {errorMessage ?? "Clip expired - retention period passed"}
      </div>
    );
  }

  if (status === "forbidden") {
    return (
      <div className="flex items-center gap-2 py-2 text-xs font-mono text-caution/80">
        <Lock className="h-3.5 w-3.5 shrink-0" />
        {errorMessage}
      </div>
    );
  }

  if (status === "unavailable" || status === "error") {
    return (
      <div className="flex items-center gap-2 py-2 text-xs font-mono text-mist/50">
        <Ban className="h-3.5 w-3.5 shrink-0" />
        {errorMessage ?? "Footage unavailable"}
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-brand-gunmetal">
      <div className="flex items-center justify-between gap-2 border-b border-brand-gunmetal bg-brand-void/40 px-3 py-1.5">
        <div className="flex min-w-0 items-center gap-2">
          <Film className="h-3 w-3 shrink-0 text-brand-pulse" />
          <span className="truncate text-xs font-mono text-mist/70">
            {current.label} · {formattedTimestamp}
          </span>
        </div>

        {playlist.length > 1 && (
          <span className="shrink-0 rounded-full bg-brand-green/10 px-2 py-0.5 text-[10px] text-brand-green">
            {index + 1} / {playlist.length}
          </span>
        )}
      </div>

      <video
        key={current.id}
        src={url ?? undefined}
        controls
        autoPlay
        muted
        playsInline
        onLoadedMetadata={(event) => {
          event.currentTarget.playbackRate = 0.5;
        }}
        onEnded={() => {
          setIndex((previous) =>
            previous < playlist.length - 1 ? previous + 1 : previous,
          );
        }}
        className="max-h-56 w-full bg-brand-void"
        aria-label={`Detection footage at ${formattedTimestamp}`}
      />
    </div>
  );
}
