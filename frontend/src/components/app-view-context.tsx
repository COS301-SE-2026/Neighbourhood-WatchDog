"use client"

import { createContext, useContext, useEffect, useMemo, useState } from "react"

export type AppSection = "dashboard" | "alerts" | "join" | "reports" | "settings"

type AppViewState = {
  section: AppSection
  propertyId: string | null
  setSection: (section: AppSection) => void
  setPropertyView: (propertyId: string | null) => void
}

const STORAGE_KEY = "watchdog-app-view"

const AppViewContext = createContext<AppViewState | null>(null)

export function AppViewProvider({ children }: { children: React.ReactNode }) {
  const [section, setSectionState] = useState<AppSection>("dashboard")
  const [propertyId, setPropertyId] = useState<string | null>(null)

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY)
      if (!saved) return

      const parsed = JSON.parse(saved) as {
        section?: AppSection
        propertyId?: string | null
      }

      if (parsed.section) {
        // eslint-disable-next-line
        setSectionState(parsed.section)
      }
      if (typeof parsed.propertyId === "string" || parsed.propertyId === null) {
        // eslint-disable-next-line
        setPropertyId(parsed.propertyId ?? null)
      }
    } catch {
      // Ignore invalid persisted view state and fall back to dashboard.
    }
  }, [])

  useEffect(() => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ section, propertyId }),
    )
  }, [propertyId, section])

  const value = useMemo<AppViewState>(
    () => ({
      section,
      propertyId,
      setSection: (nextSection) => {
        setSectionState(nextSection)
        if (nextSection !== "dashboard") {
          setPropertyId(null)
        }
      },
      setPropertyView: (nextPropertyId) => {
        setSectionState("dashboard")
        setPropertyId(nextPropertyId)
      },
    }),
    [propertyId, section],
  )

  return <AppViewContext.Provider value={value}>{children}</AppViewContext.Provider>
}

export function useAppView() {
  const context = useContext(AppViewContext)
  if (!context) {
    throw new Error("useAppView must be used within an AppViewProvider")
  }

  return context
}