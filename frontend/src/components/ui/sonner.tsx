"use client"

import { useTheme } from "next-themes"
import { Toaster as Sonner, type ToasterProps } from "sonner"
import { CircleCheckIcon, InfoIcon, TriangleAlertIcon, OctagonXIcon, Loader2Icon } from "lucide-react"

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme()

  return (
    <Sonner
      richColors
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      icons={{
        success: <CircleCheckIcon className="size-4" />,
        info: <InfoIcon className="size-4" />,
        warning: <TriangleAlertIcon className="size-4" />,
        error: <OctagonXIcon className="size-4" />,
        loading: <Loader2Icon className="size-4 animate-spin" />,
      }}
      style={
        {
          "--normal-bg": "var(--toast-bg)",
          "--normal-text": "var(--toast-text)",
          "--normal-border": "var(--toast-border)",
          "--success-bg": "var(--toast-success)",
          "--success-text": "var(--toast-success-text)",
          "--warning-bg": "var(--toast-warning)",
          "--warning-text": "var(--toast-warning-text)",
          "--error-bg": "var(--toast-error)",
          "--error-text": "var(--toast-error-text)",
          "--info-bg": "var(--toast-info)",
          "--info-text": "var(--toast-info-text)",
        } as React.CSSProperties
      }
      toastOptions={{
        classNames: {
          toast: "border",
        },
      }}
      {...props}
    />
  )
}

export { Toaster }
