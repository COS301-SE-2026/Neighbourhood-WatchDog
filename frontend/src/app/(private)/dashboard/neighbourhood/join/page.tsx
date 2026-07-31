"use client";

import { useState, type ElementType, type FormEvent } from "react";
import {
  CheckCircle2,
  ChevronRight,
  Clock,
  Loader2,
  ShieldCheck,
  XCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
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
  icon: ElementType;
  color: string;
  label: string;
  done?: boolean;
  muted?: boolean;
}) {
  return (
    <div
      className={`flex items-center gap-2 text-sm ${
        muted ? "opacity-45" : ""
      }`}
    >
      <Icon className={`h-4 w-4 shrink-0 ${color}`} />
      <span className={done ? "text-foreground" : "text-muted-foreground"}>
        {label}
      </span>
    </div>
  );
}

function PendingState({ request }: { request: JoinRequest }) {
  return (
    <div className="space-y-5" role="status" aria-live="polite">
      <div>
        <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-full bg-primary/10">
          <Clock className="h-5 w-5 text-primary" />
        </div>

        <h2 className="text-lg font-semibold text-foreground">
          Request sent
        </h2>

        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          Your neighbourhood administrator can now review your request. You
          will receive access once it has been approved.
        </p>
      </div>


      <div className="rounded-lg border border-border bg-background p-3">
        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          Request ID
        </p>

        <p className="mt-1 break-all font-mono text-xs text-foreground">
          {request.id}
        </p>
      </div>

      <div className="space-y-3">
        <StatusRow
          icon={CheckCircle2}
          color="text-primary"
          label="Request submitted"
          done
        />
        <StatusRow
          icon={Clock}
          color="text-muted-foreground"
          label="Admin review in progress"
        />
        <StatusRow
          icon={ShieldCheck}
          color="text-muted-foreground"
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

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (code.trim()) {
      onSubmit(code.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-5">
      <div className="space-y-2">
        <Label
          htmlFor="join-code"
          className="text-sm font-medium text-foreground"
        >
          Join code
        </Label>

        <Input
          id="join-code"
          type="text"
          value={code}
          onChange={(event) => setCode(event.target.value.toUpperCase())}
          placeholder="e.g. NORTH-5F3A"
          maxLength={32}
          autoComplete="off"
          autoCapitalize="characters"
          spellCheck={false}
          disabled={loading}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? "join-code-error" : "join-code-hint"}
          className={[
            "border-input bg-background font-mono text-sm tracking-widest text-foreground",
            "placeholder:text-muted-foreground",
            "focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-0",
            error ? "border-destructive focus-visible:ring-destructive" : "",
          ]
            .filter(Boolean)
            .join(" ")}
        />

        {error ? (
          <p
            id="join-code-error"
            role="alert"
            className="flex items-center gap-1.5 text-xs text-destructive"
          >
            <XCircle className="h-3.5 w-3.5 shrink-0" />
            {error}
          </p>
        ) : (
          <p id="join-code-hint" className="text-xs text-muted-foreground">
            Your join code is provided by a neighbourhood administrator.
          </p>
        )}
      </div>

      <Button
        type="submit"
        disabled={!code.trim() || loading}
        className="w-full bg-primary font-semibold text-primary-foreground hover:bg-primary/90"
      >
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Sending request...
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
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : error instanceof Error
            ? error.message
            : "Could not send join request.";

      setState({ kind: "error", message });
    }
  }

  return (
  <div className="min-h-screen w-full bg-background px-6 py-10 text-foreground md:px-10">
    <div className="mx-auto max-w-3xl">
      <div className="mb-8 pb-6">
        <p className="text-sm font-medium text-primary">
          Neighbourhood
        </p>

        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-foreground">
          Join a neighbourhood
        </h1>

        <p className="mt-3 max-w-xl text-sm text-muted-foreground">
          Use the join code provided by a neighbourhood administrator to request
          access. Once your request is approved, you will be able to view the
          relevant alerts and neighbourhood activity.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-[minmax(0,1fr)_220px]">
        <Card className="rounded-xl border-border bg-card p-6 shadow-sm">
          {state.kind === "pending" ? (
            <PendingState request={state.request} />
          ) : (
            <>
              <div className="mb-6">
                <h2 className="text-base font-semibold text-foreground">
                  Enter join code
                </h2>

                <p className="mt-1 text-sm text-muted-foreground">
                  The code tells us which neighbourhood your request should be
                  sent to.
                </p>
              </div>

              <JoinForm
                onSubmit={handleSubmit}
                loading={state.kind === "loading"}
                error={state.kind === "error" ? state.message : null}
              />
            </>
          )}
        </Card>
      </div>
    </div>
  </div>
);
}