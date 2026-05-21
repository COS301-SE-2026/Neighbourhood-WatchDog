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

type RequestState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "pending"; requestId: string }
  | { kind: "error"; message: string };

async function submitJoinRequest(
  joinCode: string,
): Promise<{ requestId: string }> {
  await new Promise((res) => setTimeout(res, 1200));

  if (joinCode === "INVALID") {
    throw new Error("Invalid join code. Check the code and try again.");
  }

  return { requestId: "req-" + crypto.randomUUID() };
}

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
      <span className={done ? "text-white" : "text-[#D0D7E8]/70"}>{label}</span>
    </div>
  );
}

function PendingState({ requestId }: { requestId: string }) {
  return (
    <div className="space-y-5 py-1" role="status" aria-live="polite">
      <div className="text-center space-y-2">
        <div className="mx-auto h-12 w-12 rounded-full bg-[#3B5EDE]/15 border border-[#3B5EDE]/30 flex items-center justify-center">
          <Clock className="h-6 w-6 text-[#5B8DEF]" />
        </div>
        <p className="text-[15px] font-semibold text-white">
          Request sent — awaiting approval
        </p>
        <p className="text-sm text-[#D0D7E8]/60 max-w-[320px] mx-auto">
          Your admin has been notified. You&apos;ll receive a notification once
          your request is approved or denied. You cannot access neighbourhood
          data until approved.
        </p>
      </div>

      <Separator className="bg-[#2C3E6B]" />

      <div className="bg-[#1D2A5E] rounded-lg p-3 border border-[#2C3E6B]">
        <p className="text-[10px] text-[#D0D7E8]/50 uppercase tracking-wider mb-1">
          Request ID
        </p>
        <p className="text-xs font-mono text-[#5B8DEF] break-all">
          {requestId}
        </p>
      </div>

      <div className="space-y-2">
        <StatusRow
          icon={CheckCircle2}
          color="text-[#16A34A]"
          label="Request submitted"
          done
        />
        <StatusRow
          icon={Clock}
          color="text-[#D97706]"
          label="Admin review in progress"
        />
        <StatusRow
          icon={ShieldCheck}
          color="text-[#D0D7E8]/30"
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
          className="text-sm font-medium text-[#D0D7E8]"
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
            "bg-[#1D2A5E] border-[#2C3E6B] text-white placeholder:text-[#D0D7E8]/30",
            "font-mono tracking-widest text-sm",
            "focus-visible:ring-2 focus-visible:ring-[#3B5EDE] focus-visible:ring-offset-0",
            "transition-colors duration-100",
            error ? "border-[#DC2626]/60 focus-visible:ring-[#DC2626]" : "",
          ]
            .filter(Boolean)
            .join(" ")}
        />
        {error ? (
          <p
            id="join-code-error"
            role="alert"
            className="flex items-center gap-1.5 text-xs text-[#DC2626]"
          >
            <XCircle className="h-3.5 w-3.5 shrink-0" />
            {error}
          </p>
        ) : (
          <p id="join-code-hint" className="text-xs text-[#D0D7E8]/50">
            Ask your neighbourhood admin for a join code.
          </p>
        )}
      </div>

      <Button
        type="submit"
        disabled={!code.trim() || loading}
        className="w-full bg-[#3B5EDE] hover:bg-[#5B8DEF] text-white font-semibold transition-colors duration-100 focus-visible:ring-2 focus-visible:ring-[#3B5EDE] focus-visible:ring-offset-2 focus-visible:ring-offset-[#2C3E6B]"
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
      const { requestId } = await submitJoinRequest(code);
      setState({ kind: "pending", requestId });
    } catch (e) {
      setState({
        kind: "error",
        message:
          e instanceof Error ? e.message : "Could not send join request.",
      });
    }
  }

  return (
    /*
      Same fix as the alerts page — w-full fills the layout's content area so
      centering works relative to the space beside the sidebar, not the full viewport.
    */
    <div
      className="w-full min-h-full flex flex-col items-center justify-center px-8 py-12 bg-[#1D2A5E]"
      style={{ fontFamily: "var(--font-sans, 'Inter', system-ui, sans-serif)" }}
    >
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <h1 className="text-[32px] font-bold text-white leading-10">
            Join Neighbourhood
          </h1>
        </div>

        <Card className="bg-[#2C3E6B] border-[#2C3E6B] p-6 rounded-2xl shadow-lg">
          {state.kind === "pending" ? (
            <PendingState requestId={state.requestId} />
          ) : (
            <JoinForm
              onSubmit={handleSubmit}
              loading={state.kind === "loading"}
              error={state.kind === "error" ? state.message : null}
            />
          )}
        </Card>

        {state.kind !== "pending" && (
          <p className="text-center text-xs text-[#D0D7E8]/40 mt-5">
            Don&apos;t have a code? Contact your neighbourhood administrator.
          </p>
        )}
      </div>
    </div>
  );
}
