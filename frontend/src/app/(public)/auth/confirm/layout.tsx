import { ReactNode } from "react"

export default function ConfirmLayout({ children }: { children: ReactNode }) {
  return (
    <div
      className="min-h-screen flex items-center justify-center px-4"
      style={{
        background:
          "radial-gradient(circle at top, color-mix(in srgb, var(--color-ice) 16%, transparent), transparent 32%), linear-gradient(180deg, var(--color-ash) 0%, var(--color-frost) 100%)",
      }}
    >
      {children}
    </div>
  )
}