"use client";

import { useEffect, useState } from "react";
import {
  ShieldAlert,
  MapPin,
  Timer,
  CheckCircle2,
  XCircle,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  useDispatchNotification,
  type DispatchNotification,
} from "@/hooks/use-dispatch";

const RESPONSE_WINDOW = 120;

const DETECTION_LABELS: Record<string, string> = {
  WEAPON_DETECTED: "Weapon detected",
  FALL_DETECTED: "Fall detected",
};

function useCountdown(expiresAt: string | null): number {
  const [secondsLeft, setSecondsLeft] = useState(() =>
    expiresAt
      ? Math.max(
          0,
          Math.round((new Date(expiresAt).getTime() - Date.now()) / 1000),
        )
      : RESPONSE_WINDOW,
  );

  useEffect(() => {
    if (!expiresAt) return;

    const expiry = new Date(expiresAt).getTime();

    const update = () => {
      setSecondsLeft(Math.max(0, Math.round((expiry - Date.now()) / 1000)));
    };

    update();

    const interval = setInterval(update, 1000);

    return () => clearInterval(interval);
  }, [expiresAt]);

  return secondsLeft;
}

function RequestCard({
  notification,
  responding,
  onAccept,
  onDecline,
}: {
  notification: DispatchNotification;
  responding: boolean;
  onAccept: () => void;
  onDecline: () => void;
}) {
  const secondsLeft = useCountdown(notification.expiresAt);

  const progressPercent = Math.max(
    0,
    Math.min(100, (secondsLeft / RESPONSE_WINDOW) * 100),
  );

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;

  const title =
    DETECTION_LABELS[notification.detectionType ?? ""] ??
    "New dispatch request";

  const distance =
    notification.distance == null
      ? null
      : notification.distance >= 1000
        ? `${(notification.distance / 1000).toFixed(1)} km away`
        : `${Math.round(notification.distance)} m away`;

  const eta =
    notification.eta == null
      ? null
      : notification.eta < 60
        ? "<1 min away"
        : `~${Math.round(notification.eta / 60)} min away`;

  const locationInfo = [distance, eta].filter(Boolean).join(" · ");

  return (
    <div
      role="alertdialog"
      aria-label="New dispatch request"
      className="w-[320px] max-w-[calc(100vw-2rem)] overflow-hidden rounded-xl border-2 border-brand-threat bg-brand-depth shadow-[0_12px_32px_-8px_rgba(220,38,38,0.45)]"
    >
      <div className="h-1 bg-brand-slate">
        <div
          className="h-full bg-brand-threat transition-[width] duration-1000 ease-linear"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      <div className="p-4">
        <div className="mb-2 flex items-center justify-between">
          <span className="inline-flex items-center gap-1 rounded-full bg-brand-threat px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-brand-frost">
            <ShieldAlert className="h-3 w-3" />
            Dispatch request
          </span>

          <span className="flex items-center gap-1 font-mono text-xs tabular-nums text-brand-ash">
            <Timer className="h-3 w-3" />
            {minutes}:{seconds.toString().padStart(2, "0")}
          </span>
        </div>

        <p className="mb-1 text-sm font-semibold leading-snug text-brand-frost">
          {title}
        </p>

        {locationInfo && (
          <p className="mb-3 flex items-center gap-1 text-xs text-brand-ash">
            <MapPin className="h-3 w-3" />
            {locationInfo}
          </p>
        )}

        <div className="mt-1 flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1 border-border text-xs font-semibold text-brand-ash hover:bg-brand-slate hover:text-brand-frost"
            onClick={onDecline}
            disabled={responding}
            aria-label="Decline dispatch request"
          >
            Decline
          </Button>

          <Button
            size="sm"
            className="flex-1 bg-brand-green text-xs font-semibold text-brand-void hover:bg-brand-green"
            onClick={onAccept}
            disabled={responding}
            aria-label="Accept dispatch request"
          >
            {responding ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              "Accept"
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

function OutcomeToast({
  outcome,
}: {
  outcome: "ACCEPTED" | "DECLINED" | "EXPIRED";
}) {
  switch (outcome) {
    case "ACCEPTED":
      return (
        <div
          role="status"
          className="flex w-[320px] max-w-[calc(100vw-2rem)] items-center gap-2 rounded-xl border border-brand-green/40 bg-brand-green/10 px-4 py-3 text-sm font-medium text-brand-green shadow-lg"
        >
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          Dispatch accepted
        </div>
      );

    case "DECLINED":
      return (
        <div
          role="status"
          className="flex w-[320px] max-w-[calc(100vw-2rem)] items-center gap-2 rounded-xl border border-border bg-brand-slate px-4 py-3 text-sm font-medium text-brand-ash shadow-lg"
        >
          <XCircle className="h-4 w-4 shrink-0" />
          Dispatch declined
        </div>
      );

    case "EXPIRED":
      return (
        <div
          role="status"
          className="flex w-[320px] max-w-[calc(100vw-2rem)] items-center gap-2 rounded-xl border border-brand-caution/40 bg-brand-caution/10 px-4 py-3 text-sm font-medium text-brand-caution shadow-lg"
        >
          <Timer className="h-4 w-4 shrink-0" />
          Request expired
        </div>
      );
  }
}

export function DispatchRequestPopup() {
  const { notification, responding, outcome, accept, decline } =
    useDispatchNotification();

  if (!notification && !outcome) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-1200">
      {notification ? (
        <RequestCard
          notification={notification}
          responding={responding}
          onAccept={accept}
          onDecline={decline}
        />
      ) : outcome ? (
        <OutcomeToast outcome={outcome} />
      ) : null}
    </div>
  );
}
