"use client"

import { useCallback, useEffect, useState } from "react"
import { Card, CardContent } from "../ui/card"
import { Loader2 } from "lucide-react"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select"
import type { DutyStatus } from "@/lib/validators/neighbourhood"
import { getSecurityAvailability, updateSecurityAvailability } from "@/lib/api/neighbourhood"
import { cn } from "@/lib/utils"
import { useLocationPermission } from "@/hooks/use-location-permission"
import { useOfficerLocationTracking } from "@/hooks/use-officer-location-tracking"
import { LocationPermissionDialog } from "../shared/LocationPermissionDialog"
import { Capacitor } from "@capacitor/core" 
import { BackgroundLocationPermissionDialog } from "../shared/BackgroundLocationPermissionDialog"

const STALE_LOCATION_THRESHOLD_MS = 120_000

const STATUS_OPTIONS: { value: DutyStatus; label: string; dotClass: string }[] = [
  { value: "ON_DUTY", label: "On Duty", dotClass: "bg-brand-green" },
  { value: "OFF_DUTY", label: "Off Duty", dotClass: "bg-brand-ash" },
]
interface StatusToggleInterface {
  readonly neighbourhoodId: string
}

export default function StatusToggle({ neighbourhoodId }: StatusToggleInterface) {
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState<boolean>(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [isStale, setIsStale] = useState(true)

  const [officerStatus, setOfficerStatus] = useState<DutyStatus | null>(null)
  const [locationUpdatedAt, setLocationUpdatedAt] = useState<Date | null>(null)
  const [showBackgroundPermissionDialog, setShowBackgroundPermissionDialog] = useState<boolean>(false)

  const { 
    status: permissionStatus, 
    refresh: refreshPermission,
    backgroundStatus,
  } = useLocationPermission()
  const [showPermissionDialog, setShowPermissionDialog] = useState(false)
  const [showUnsupportedNote, setShowUnsupportedNote] = useState(false)
  const [permissionBlocked, setPermissionBlocked] = useState(false)


  const loadAvailability = useCallback(
    async (signal?: { cancelled: boolean }, silent = false) => {
      if (!silent) setLoading(true)
      setError(null)
        
      try {
        const res = await getSecurityAvailability(neighbourhoodId)
        if (signal?.cancelled) return

        setOfficerStatus((res.availability == "AVAILABLE" || res.availability == "BUSY") ? "ON_DUTY" : "OFF_DUTY")
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
    const interval = setInterval(() => {
      loadAvailability(undefined, true)
    }, 30_000)

    return () => {
      clearInterval(interval)
    }
  }, [loadAvailability])

  useEffect(() => {
    const signal = { cancelled: false }
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadAvailability(signal)

    return () => {
      signal.cancelled = true
    }
  }, [neighbourhoodId])

  useEffect(() => {
    const computeStale = () => {
      setIsStale(
        locationUpdatedAt === null ||
        Date.now() - locationUpdatedAt.getTime() > STALE_LOCATION_THRESHOLD_MS
      )
    }
    computeStale()
    const interval = setInterval(computeStale, 30_000)
    return () => clearInterval(interval)
  })

  const handleStatusChange = async (next: DutyStatus) => {
    if (next === "ON_DUTY" && !Capacitor.isNativePlatform()) {
      setShowUnsupportedNote(true)
      return 
    }

    if (next === "ON_DUTY" && permissionStatus !== "granted") {
      setPermissionBlocked(true)
      setShowPermissionDialog(true)
      return 
    }

    setPermissionBlocked(false)
    setShowUnsupportedNote(false)
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

  useOfficerLocationTracking(neighbourhoodId, officerStatus === "ON_DUTY")

  if (loading) {
    return (
      <Card className="px-6 py-8 text-foreground md:px-8">
        <CardContent className="flex items-center justify-center p-0 py-6">
          <Loader2 className="size-5 animate-spin text-brand-green"/>
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
            className="text-sm font-medium underline underline-offset-2 cursor-pointer"
          >
            Retry
          </button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div>
    <Card className="px-6 py-5 text-foreground md:px-8">
      <CardContent className="space-y-3 p-0">
        <div className="flex items-center gap-3">
          <b>Status:</b>
          <Select
            value={officerStatus ?? undefined}
            onValueChange={(value) => handleStatusChange(value as DutyStatus)}
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
    </Card>
    {permissionBlocked && (
      <div className="flex items-center gap-2 text-sm text-destructive">
        <span>Location permission is required to go on duty.</span>
        <button
          type="button"
          onClick={() => handleStatusChange("ON_DUTY")}
          className="font-medium underline underline-offset-2 cursor-pointer">
            Retry
        </button>
      </div>
    )}
    {showUnsupportedNote && (
      <div className="text-sm px-5 py-5 text-brand-ash">
        Going on duty requires the WatchDog mobile app to share your location.
        Please switch to your phone to go on duty.
      </div>
    )}
    {officerStatus === "ON_DUTY" && backgroundStatus !== "granted" && (
      <div className="flex items-center gap-2 text-sm text-brand-ash px-5">
        <span>
          Location will stop sharing if you leave the app. Enable &quot;Allow all the time&quot; to keep sharing while on duty.
        </span>
        <button
          type="button"
          onClick={() => setShowBackgroundPermissionDialog(true)}
          className="font-medium underline-offset-2 cursor-pointer whitespace-nowrap">
            Enable
        </button>
      </div>
    )}
    <LocationPermissionDialog
      open={showPermissionDialog}
      onOpenChange={(open) => {
        setShowPermissionDialog(open)
        if (!open) refreshPermission()
      }}
    />
    <BackgroundLocationPermissionDialog
      open={showBackgroundPermissionDialog}
      onOpenChange={setShowBackgroundPermissionDialog}/>
    </div>
  )
}