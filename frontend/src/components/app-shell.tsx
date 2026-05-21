"use client"

import DashboardPage from "@/app/dashboard/page"
import AlertsPage from "@/app/alert/page"
import JoinNeighbourhoodPage from "@/app/joinNeighbourhood/page"
import PropertyPage from "@/app/property-page/page"
import { Card } from "@/components/ui/card"
import { useAppView } from "@/components/app-view-context"

function Placeholder({ title, description }: { title: string; description: string }) {
  return (
    <div className="watchdog-page-shell watchdog-page-shell--center">
      <Card className="w-full max-w-2xl p-8 rounded-2xl watchdog-surface-strong text-white">
        <h1 className="watchdog-heading text-white">{title}</h1>
        <p className="mt-3 watchdog-text-subtle">{description}</p>
      </Card>
    </div>
  )
}

export function AppShell() {
  const { section, propertyId } = useAppView()

  if (section === "alerts") {
    return <AlertsPage />
  }

  if (section === "join") {
    return <JoinNeighbourhoodPage />
  }

  if (section === "reports") {
    return (
      <Placeholder
        title="Reports"
        description="This section is ready for report summaries and exports."
      />
    )
  }

  if (section === "settings") {
    return (
      <Placeholder
        title="Settings"
        description="This section will hold profile, alert, and system preferences."
      />
    )
  }

  if (propertyId) {
    return <PropertyPage />
  }

  return <DashboardPage />
}