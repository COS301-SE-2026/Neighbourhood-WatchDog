import { ReactNode } from "react";

export default function LoginLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div
      className="dark flex min-h-screen items-center justify-center px-4 text-foreground"
      style={{
        background:
          "radial-gradient(circle at top, color-mix(in srgb, var(--color-ice) 14%, transparent), transparent 38%), var(--background)",
      }}
    >
      {children}
    </div>
  );
}