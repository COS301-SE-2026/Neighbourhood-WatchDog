"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  ChevronRight,
  ShieldCheck,
} from "lucide-react";
import { submitJoinRequest, ApiError } from "@/lib/api/neighbourhoodJoin";
import type { JoinRequest } from "@/components/shared/RequestCard";

type RequestState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "pending"; request: JoinRequest }
  | { kind: "error"; message: string };

function StatusRow({
  icon: Icon,
  color,
  label,
  done = false,
  muted = false,
}: {
  icon: React.ElementType;
  color: string;
  label: string;
  done?: boolean;
  muted?: boolean;
}) {
  return (
    <div
      className={`flex items-center gap-2 text-sm ${muted ? "opacity-40" : ""}`}
    >
      <Icon className={`h-4 w-4 shrink-0 ${color}`} />
      <span className={done ? "text-white" : "text-mist/70"}>{label}</span>
    </div>
  );
}

function PendingState({ request }: { request: JoinRequest }) {
  return (
    <div className="space-y-5 py-1" role="status" aria-live="polite">
      <div className="text-center space-y-2">
        <div className="mx-auto h-12 w-12 rounded-full bg-blue/15 border border-blue/30 flex items-center justify-center">
          <Clock className="h-6 w-6 text-sky" />
        </div>
        <p className="text-base font-semibold text-white">
          Request sent — awaiting approval
        </p>
        <p className="text-sm text-mist/60 max-w-[320px] mx-auto">
          Your admin has been notified. You&apos;ll receive a notification once
          your request is approved or denied. You cannot access neighbourhood
          data until approved.
        </p>
      </div>

      <Separator className="bg-steel" />

      <div className="bg-navy rounded-lg p-3 border border-steel">
        <p className="text-xs text-mist/50 uppercase tracking-wider mb-1">
          Request ID
        </p>
        <p className="text-xs font-mono text-sky break-all">
          {request.id}
        </p>
      </div>

      <div className="space-y-2">
        <StatusRow
          icon={CheckCircle2}
          color="text-safe"
          label="Request submitted"
          done
        />
        <StatusRow
          icon={Clock}
          color="text-caution"
          label="Admin review in progress"
        />
        <StatusRow
          icon={ShieldCheck}
          color="text-mist/30"
          label="Access granted"
          muted
        />
      </div>
    </div>
  );
}

function JoinForm({
  onSubmit,
  loading,
  error,
}: {
  onSubmit: (code: string) => void;
  loading: boolean;
  error: string | null;
}) {
  const [code, setCode] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (code.trim()) onSubmit(code.trim());
  };

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-5">
      <div className="space-y-2">
        <Label
          htmlFor="join-code"
          className="text-sm font-medium text-mist"
        >
          Join code
        </Label>
        <Input
          id="join-code"
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value.toUpperCase())}
          placeholder="e.g. NORTH-5F3A"
          maxLength={32}
          autoComplete="off"
          autoCapitalize="characters"
          spellCheck={false}
          aria-describedby={error ? "join-code-error" : "join-code-hint"}
          aria-invalid={!!error}
          disabled={loading}
          className={[
            "bg-navy border-steel text-white placeholder:text-mist/30",
            "font-mono tracking-widest text-sm",
            "focus-visible:ring-2 focus-visible:ring-blue focus-visible:ring-offset-0",
            "transition-colors duration-100",
            error ? "border-threat/60 focus-visible:ring-threat" : "",
          ]
            .filter(Boolean)
            .join(" ")}
        />
        {error ? (
          <p
            id="join-code-error"
            role="alert"
            className="flex items-center gap-1.5 text-xs text-threat"
          >
            <XCircle className="h-3.5 w-3.5 shrink-0" />
            {error}
          </p>
        ) : (
          <p id="join-code-hint" className="text-xs text-mist/50">
            Ask your neighbourhood admin for a join code.
          </p>
        )}
      </div>

      <Button
        type="submit"
        disabled={!code.trim() || loading}
        className="w-full bg-blue hover:bg-sky text-white font-semibold transition-colors duration-100 focus-visible:ring-2 focus-visible:ring-blue focus-visible:ring-offset-2 focus-visible:ring-offset-steel"
      >
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Sending request…
          </>
        ) : (
          <>
            Request to join
            <ChevronRight className="ml-2 h-4 w-4" />
          </>
        )}
      </Button>
    </form>
  );
}

export default function JoinNeighbourhoodPage() {
  const [state, setState] = useState<RequestState>({ kind: "idle" });

  async function handleSubmit(code: string) {
    setState({ kind: "loading" });
    try {
      const request = await submitJoinRequest(code);
      setState({ kind: "pending", request });
    } catch (e) {
      const message =
        e instanceof ApiError
          ? e.message
          : e instanceof Error
            ? e.message
            : "Could not send join request.";
      setState({ kind: "error", message });
    }
  }

  return (
    <div
      className="w-full min-h-full flex flex-col items-center justify-center px-8 py-12 bg-navy"
      style={{ fontFamily: "var(--font-sans, 'Inter', system-ui, sans-serif)" }}
    >
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <h1 className="text-[2rem] font-bold text-white leading-10">
            Join Neighbourhood
          </h1>
        </div>

        <Card className="bg-steel border-steel p-6 rounded-xl shadow-lg">
          {state.kind === "pending" ? (
            <PendingState request={state.request} />
          ) : (
            <JoinForm
              onSubmit={handleSubmit}
              loading={state.kind === "loading"}
              error={state.kind === "error" ? state.message : null}
            />
          )}
        </Card>

        {state.kind !== "pending" && (
          <p className="text-center text-xs text-mist/40 mt-5">
            Don&apos;t have a code? Contact your neighbourhood administrator.
          </p>
        )}
      </div>
    </div>
  );
}
