"use client";

import { useState } from "react";
import { Check, Copy, KeyRound, Loader2, RefreshCw} from "lucide-react";


import { getPairingToken } from "@/lib/api/pairAgent";
import { Button } from "@/components/ui/button";


interface PairAgentProps {
  propertyId: string;
  propertyAddress: string;
}

export default function PairAgent({ propertyId, propertyAddress}: Readonly<PairAgentProps>) {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const getToken = async () => {
    try {
      setLoading(true);
      setError(null);
      setCopied(false);

      const tokenResponse = await getPairingToken(propertyId);

      if (
        !tokenResponse ||
        tokenResponse.status !== 200 ||
        !tokenResponse.data?.token
      ) {
        throw new Error("Could not generate a pairing token. Please try again.");
      }

      setToken(tokenResponse.data.token);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "An unexpected error occurred while generating the token."
      );
    } finally {
      setLoading(false);
    }
  };

  const copyToken = async () => {
    if (!token) return;

    await navigator.clipboard.writeText(token);
    setCopied(true);

    window.setTimeout(() => {
      setCopied(false);
    }, 2000);
  };

  return (
      <div className="w-full">
        <div className="mb-1.5 flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
          <KeyRound className="h-4.5 w-4.5 text-primary" />
        </div>
        <h2 className="mt-2 text-card-foreground">Pair security agent</h2>

        <p className="mt-3 text-sm">
          Property:
          <span className="mt-1 block font-medium text-foreground">{propertyAddress}</span>
        </p>

        <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
          Generate a one-time token to securely connect a WatchDog edge agent to the selected property.
        </p>

      <div className="mt-6 space-y-5">
        {error && (
          <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-brand-threat">
            {error}
          </div>
        )}

        {!token && !error && (
          <div className="rounded-lg border border-border bg-background px-4 py-3 text-sm text-muted-foreground">
            A token is required before an edge agent can send camera detections for this property.
          </div>
        )}

        {token && (
          <div className="rounded-xl border border-primary/30 bg-primary/10 p-4">
            <p className="text-xs font-medium uppercase tracking-wider text-primary">Pairing token</p>
            <p className="mt-2 break-all font-mono text-sm text-foreground">{token}</p>

            <Button
              type="button"
              variant="outline"
              onClick={copyToken}
              className="mt-5 min-h-11 w-full border-border bg-background text-sm font-medium text-foreground hover:bg-accent"
            >
              {copied ? (
                <>
                  <Check className="mr-2 h-4 w-4 text-primary" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="mr-2 h-4 w-4" />
                  Copy token
                </>
              )}
            </Button>
          </div>
        )}
      </div>

      <div className="mt-6">
        <Button
          type="button"
          onClick={getToken}
          disabled={loading}
          className="min-h-12 w-full bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating token...
            </>
          ) : token ? (
            <>
              <RefreshCw className="mr-2 h-4 w-4" />
              Regenerate token
            </>
          ) : (
            <>
              <KeyRound className="mr-2 h-4 w-4" />
              Generate pairing token
            </>
          )}
        </Button>
      </div>
    </div>
  );
}