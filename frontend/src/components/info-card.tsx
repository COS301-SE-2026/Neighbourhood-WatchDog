"use client"

import { Card } from "@/components/ui/card"

interface InfoCardProps {
  title: string
  children: React.ReactNode
}

export function InfoCard({ title, children }: InfoCardProps) {
  return (
    <Card className="!bg-navy text-black rounded-lg p-6">
      <h2 className="text-xl font-bold mb-4">{title}</h2>
      <div className="text-sm">{children}</div>
    </Card>
  )
}