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

const now = new Date();
const minsAgo = (m: number) =>
  new Date(now.getTime() - m * 60_000).toISOString();

const MOCK_REQUESTS: JoinRequest[] = [
  {
    id: "req-a1b2c3d4-0001",
    neighbourhood_id: "nbh-f3a9b201-0001",
    user_id: "usr-00000001-0001",
    user_name: "Sipho Dlamini",
    status: "PENDING",
    created_at: minsAgo(5),
    resolved_at: null,
  },
  {
    id: "req-a1b2c3d4-0002",
    neighbourhood_id: "nbh-f3a9b201-0001",
    user_id: "usr-00000002-0002",
    user_name: "Priya Naidoo",
    status: "PENDING",
    created_at: minsAgo(18),
    resolved_at: null,
  },
  {
    id: "req-a1b2c3d4-0003",
    neighbourhood_id: "nbh-f3a9b201-0001",
    user_id: "usr-00000003-0003",
    user_name: "Marco van Wyk",
    status: "PENDING",
    created_at: minsAgo(45),
    resolved_at: null,
  },
  {
    id: "req-a1b2c3d4-0004",
    neighbourhood_id: "nbh-f3a9b201-0001",
    user_id: "usr-00000004-0004",
    user_name: "Aisha Mokoena",
    status: "APPROVED",
    created_at: minsAgo(200),
    resolved_at: minsAgo(150),
  },
  {
    id: "req-a1b2c3d4-0005",
    neighbourhood_id: "nbh-f3a9b201-0001",
    user_id: "usr-00000005-0005",
    user_name: "Thabo Khumalo",
    status: "DENIED",
    created_at: minsAgo(400),
    resolved_at: minsAgo(360),
  },
];

const ALL_STATUSES: JoinRequestStatus[] = ["PENDING", "APPROVED", "DENIED"];

const STATUS_LABELS: Record<JoinRequestStatus | "ALL", string> = {
  ALL: "All",
  PENDING: "Pending",
  APPROVED: "Approved",
  DENIED: "Denied",
};
