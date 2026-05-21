"use client";

import { useCallback, useMemo, useState } from "react";
import {
  RequestCard,
  type JoinRequest,
  type JoinRequestStatus,
} from "@/components/shared/RequestCard";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { RefreshCw } from "lucide-react";

const ALL_STATUSES: JoinRequestStatus[] = ["PENDING", "APPROVED", "DENIED"];

const STATUS_LABELS: Record<JoinRequestStatus | "ALL", string> = {
  ALL: "All",
  PENDING: "Pending",
  APPROVED: "Approved",
  DENIED: "Denied",
};

type FilterValue = JoinRequestStatus | "ALL";

function EmptyState({ filter }: { filter: FilterValue }) {
  return (
    <div
      className="flex flex-col items-center justify-center py-16 text-center"
      role="status"
      aria-live="polite"
    >
      <p className="text-[15px] font-semibold text-white/50">
        No {filter === "ALL" ? "" : STATUS_LABELS[filter].toLowerCase()}{" "}
        requests
      </p>
    </div>
  );
}

export default function JoinRequestsPage() {
  const [requests, setRequests] = useState<JoinRequest[]>(MOCK_REQUESTS);
  const [refreshKey, setRefreshKey] = useState(0);
  const [activeFilter, setActiveFilter] = useState<FilterValue>("PENDING");

  const handleApprove = useCallback(async (id: string) => {
    // Simulate network latency
    await new Promise((res) => setTimeout(res, 900));
    setRequests((prev) =>
      prev.map((r) =>
        r.id === id
          ? {
              ...r,
              status: "APPROVED" as JoinRequestStatus,
              resolved_at: new Date().toISOString(),
            }
          : r,
      ),
    );
  }, []);

  const handleDeny = useCallback(async (id: string) => {
    await new Promise((res) => setTimeout(res, 900));
    setRequests((prev) =>
      prev.map((r) =>
        r.id === id
          ? {
              ...r,
              status: "DENIED" as JoinRequestStatus,
              resolved_at: new Date().toISOString(),
            }
          : r,
      ),
    );
  }, []);

  function handleRefresh() {
    setRequests(MOCK_REQUESTS);
    setRefreshKey((k) => k + 1);
    setActiveFilter("PENDING");
  }

  const filtered = useMemo(
    () =>
      activeFilter === "ALL"
        ? requests
        : requests.filter((r) => r.status === activeFilter),
    [requests, activeFilter],
  );

  const pendingCount = requests.filter((r) => r.status === "PENDING").length;

  return (
    <div
      className="w-full flex flex-col items-center px-8 py-10 bg-[#1D2A5E] min-h-full"
      style={{
        fontFamily: "var(--font-sans, 'Inter', system-ui, sans-serif)",
      }}
    >
      <div className="w-full max-w-2xl">
        <header className="mb-6 text-center">
          <h1 className="text-[32px] font-bold leading-10 text-white">
            Join Requests
          </h1>

          {pendingCount > 0 && (
            <div
              className="flex gap-2 mt-3 flex-wrap justify-center"
              aria-live="polite"
            >
              <span className="inline-flex items-center gap-1 text-xs font-semibold bg-[#3B5EDE]/20 border border-[#3B5EDE]/30 rounded-full px-3 py-1 text-[#5B8DEF]">
                {pendingCount} pending
              </span>
            </div>
          )}
        </header>

        <Card className="bg-[#2C3E6B]/40 border-[#2C3E6B] rounded-2xl">
          {/* Toolbar */}
          <div className="flex items-center justify-between gap-3 px-5 py-4 border-b border-[#2C3E6B] rounded-t-2xl">
            {/* Filter tabs */}
            <div className="flex items-center bg-[#1D2A5E]/70 border border-[#2C3E6B] rounded-lg overflow-hidden">
              {(
                ["PENDING", ...ALL_STATUSES.slice(1), "ALL"] as FilterValue[]
              ).map((f, i, arr) => (
                <button
                  key={f}
                  type="button"
                  onClick={() => setActiveFilter(f)}
                  className={[
                    "text-[11px] font-medium px-3 py-1.5 transition-colors duration-100",
                    i < arr.length - 1 ? "border-r border-[#2C3E6B]" : "",
                    activeFilter === f
                      ? "bg-[#3B5EDE]/25 text-[#5B8DEF]"
                      : "text-[#D0D7E8] hover:bg-[#2C3E6B] hover:text-white",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  {STATUS_LABELS[f]}
                </button>
              ))}
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              className="text-[#5B8DEF] hover:text-white hover:bg-[#2C3E6B] transition-colors text-xs"
              aria-label="Refresh requests"
            >
              <RefreshCw key={refreshKey} className="h-3.5 w-3.5 mr-1.5" />
              Refresh
            </Button>
          </div>

          {/* List */}
          <section
            aria-label="Join request list"
            aria-live="polite"
            className="p-4 rounded-b-2xl"
          >
            {filtered.length === 0 ? (
              <EmptyState filter={activeFilter} />
            ) : (
              <div className="space-y-2.5">
                {filtered.map((req) => (
                  <RequestCard
                    key={req.id}
                    request={req}
                    onApprove={handleApprove}
                    onDeny={handleDeny}
                  />
                ))}
              </div>
            )}
          </section>
        </Card>
      </div>
    </div>
  );
}
