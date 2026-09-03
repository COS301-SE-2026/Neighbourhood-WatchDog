"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  Loader2,
  Mail,
  ShieldCheck,
  UserRound,
  Users,
} from "lucide-react";

import { getPropertyMembers } from "@/lib/api/property";
import type { PropertyMembers } from "@/lib/validators/property";

export default function PropertyMembers() {
  const { propertyId } = useParams<{
    propertyId: string;
  }>();

  const [members, setMembers] = useState<
    PropertyMembers["members"]
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    getPropertyMembers(propertyId)
      .then((result) => {
        if (cancelled) {
          return;
        }

        setMembers(result.members);
      })
      .catch((requestError: unknown) => {
        if (cancelled) {
          return;
        }

        setError(
          requestError instanceof Error
            ? requestError.message
            : "Failed to load property members.",
        );
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [propertyId]);

  return (
    <main className="min-h-full bg-background px-6 py-8 text-foreground md:px-8">
      <div className="mx-auto w-full max-w-6xl">
        <header className="border-b border-border pb-6">
          <p className="text-sm text-primary">
            My home
          </p>

          <div className="mt-2 flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-lg border border-primary/25 bg-primary/10">
              <Users className="size-5 text-primary" />
            </div>

            <div>
              <h1 className="text-2xl font-semibold tracking-tight">
                Property members
              </h1>

              <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                Manage the people who have access to this property.
              </p>
            </div>
          </div>
        </header>

        <section className="mt-7">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">
                Members
              </h2>

              <p className="mt-1 text-sm text-muted-foreground">
                Users currently connected to this property.
              </p>
            </div>

            {!loading && !error && (
              <span className="rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground">
                {members.length}{" "}
                {members.length === 1
                  ? "member"
                  : "members"}
              </span>
            )}
          </div>

          {loading ? (
            <div className="flex items-center justify-center rounded-xl border border-border bg-card py-20">
              <Loader2 className="size-5 animate-spin text-primary" />
            </div>
          ) : error ? (
            <div
              role="alert"
              className="rounded-xl border border-destructive/30 bg-destructive/10 px-5 py-4 text-sm text-destructive"
            >
              {error}
            </div>
          ) : members.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card px-6 py-16 text-center">
              <div className="flex size-12 items-center justify-center rounded-full bg-muted">
                <UserRound className="size-5 text-muted-foreground" />
              </div>

              <h3 className="mt-4 text-sm font-semibold">
                No members yet
              </h3>

              <p className="mt-1 text-sm text-muted-foreground">
                Property members will appear here.
              </p>
            </div>
          ) : (
            <div className="overflow-hidden rounded-xl border border-border bg-card">
              <div className="divide-y divide-border">
                {members.map((member) => {
                  const fullName = [
                    member.first_name,
                    member.last_name,
                  ]
                    .filter(Boolean)
                    .join(" ");

                  return (
                    <div
                      key={member.user_id}
                      className="flex items-center justify-between gap-4 px-5 py-4 transition-colors hover:bg-muted/40"
                    >
                      <div className="flex min-w-0 items-center gap-3">
                        <div className="flex size-9 shrink-0 items-center justify-center rounded-full border border-primary/25 bg-primary/10">
                          <UserRound className="size-4 text-primary" />
                        </div>

                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium">
                            {fullName || member.email}
                          </p>

                          <p className="mt-0.5 flex items-center gap-1 truncate text-xs text-muted-foreground">
                            <Mail className="size-3" />
                            {member.email}
                          </p>
                        </div>
                      </div>

                      {member.is_admin && (
                        <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-primary/25 bg-primary/10 px-2.5 py-1 text-xs text-primary">
                          <ShieldCheck className="size-3.5" />
                          Admin
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
