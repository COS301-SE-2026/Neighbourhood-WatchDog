"use client"

import { useCallback, useEffect, useState } from "react"
import { Card, CardAction, CardContent } from "../ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select"
import type { AvailabilityStatus } from "@/lib/validators/neighbourhood"
import { getSecurityAvailability, updateSecurityAvailability } from "@/lib/api/neighbourhood"
import { cn } from "@/lib/utils"

const STALE_LOCATION_THRESHOLD_MS = 120_000

const STATUS_OPTIONS: { value: AvailabilityStatus; label: string; dotClass: string }[] = [
  { value: "AVAILABLE", label: "Available", dotClass: "bg-brand-green" },
  { value: "BUSY", label: "Busy", dotClass: "bg-yellow-500" },
  { value: "UNAVAILABLE", label: "Unavailable", dotClass: "bg-brand-ash" },
]
interface StatusToggleInterface {
  readonly neighbourhoodId: string
}

export default function StatusToggle({ neighbourhoodId }: StatusToggleInterface) {
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState<boolean>(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  const [officerStatus, setOfficerStatus] = useState<AvailabilityStatus | null>(null)
  const [locationUpdatedAt, setLocationUpdatedAt] = useState<Date | null>(null)
  
  const loadAvailability = useCallback(
    async (signal?: { cancelled: boolean }) => {
      setLoading(true)
      setError(null)
        
      try {
        const res = await getSecurityAvailability(neighbourhoodId)
        if (signal?.cancelled) return

        setOfficerStatus(res.availability)
        setLocationUpdatedAt(res.location_updated_at ? new Date(res.location_updated_at) : null)
      } catch (err) {
        if (signal?.cancelled) return
        setError(err instanceof Error ? err.message : "Failed to load status")
      } finally {
        if (!signal?.cancelled) setLoading(false)
      }
    }, [neighbourhoodId],
  )

  useEffect(() => {
    const signal = { cancelled: false }
    loadAvailability(signal)

    return () => {
      signal.cancelled = true
    }
  }, [neighbourhoodId])

  const handleStatusChange = async (next: AvailabilityStatus) => {
    const previous = officerStatus
    setOfficerStatus(next)
    setSaveError(null)
    setSaving(true)

    try {
      await updateSecurityAvailability(neighbourhoodId, next)
    } catch (err) {
      setOfficerStatus(previous)
      setSaveError(err instanceof Error ? err.message : "Failed to update status")
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <Card className="px-6 py-8 text-foreground md:px-8">
        <CardContent className="space-y-2 p-0">
          <div className="h-4 w-24 animate-pulse rounded bg-brand-slate"></div>
          <div className="h-4 w-40 animate-pulse rounded bg-brand-slate"></div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="px-6 py-8 text-foreground md:px-8">
        <CardContent className="space-y-3 p-0">
          <p className="text-sm text-destructive">{error}</p>
          <button
            type="button"
            onClick={() => loadAvailability()}
            className="text-sm font-medium underline underline-offset-2"
          >
            Retry
          </button>
        </CardContent>
      </Card>
    )
  }

  const isStale =
    locationUpdatedAt === null ||
    Date.now() - locationUpdatedAt.getTime() > STALE_LOCATION_THRESHOLD_MS

  return (
    <Card className="px-6 py-8 text-foreground md:px-8">
      <CardContent className="space-y-3 p-0">
        <div className="flex items-center gap-3">
          <b>Status:</b>
          <Select
            value={officerStatus ?? undefined}
            onValueChange={(value) => handleStatusChange(value as AvailabilityStatus)}
            disabled={saving}
          >
            <SelectTrigger className="w-40">
              <SelectValue>
                <span className="flex items-center gap-3">
                  <span
                    className={cn(
                      "size-2 rounded-full",
                      STATUS_OPTIONS.find((o) => o.value === officerStatus)?.dotClass,
                    )}
                  />
                  {STATUS_OPTIONS.find((o) => o.value === officerStatus)?.label ?? "Unknown"}
                </span>
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              {STATUS_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  <span className="flex items-center gap-3">
                    <span className={cn("size-2 rounded-full", option.dotClass)}/>
                    {option.label}
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        {saveError && <p className="text-xs text-destructive">{saveError}</p>}
        <div className="flex items-center gap-2">
          <b>Location:</b>
          <span className={cn("size-2 rounded-full", isStale ? "bg-brand-ash" : "bg-brand-green")}/>
          <span className="text-sm text-brand-ash">
            {locationUpdatedAt
              ? `Last sent ${locationUpdatedAt.toLocaleString()}`
              : "No location received yet"}
          </span>
        </div>
      </CardContent>

      <CardAction/>
    </Card>
  )
}