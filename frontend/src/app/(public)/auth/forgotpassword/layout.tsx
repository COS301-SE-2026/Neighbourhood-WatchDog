import { ReactNode } from "react"

export default function ForgotPasswordLayout({ children }: { children: ReactNode }) {
  return (
    <div
      className="min-h-screen flex items-center justify-center px-4"
      style={{
        background:
          "radial-gradient(circle at top, color-mix(in srgb, var(--color-sky) 16%, transparent), transparent 32%), linear-gradient(180deg, var(--color-fog) 0%, var(--color-white) 100%)",
      }}
    >
      {children}
    </div>
  )
}