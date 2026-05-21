import { ReactNode } from "react"

export default function LoginLayout({ children }: { children: ReactNode }) {
  return (
    <div
      className="min-h-screen flex items-center justify-center px-4"
      style={{
        background:
          "radial-gradient(circle at top, rgba(91, 141, 239, 0.16), transparent 32%), linear-gradient(180deg, var(--color-fog) 0%, #ffffff 100%)",
      }}
    >
      {children}
    </div>
  )
}