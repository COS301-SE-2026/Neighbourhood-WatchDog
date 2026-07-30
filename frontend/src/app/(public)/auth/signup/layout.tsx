import { ReactNode } from "react";

export default function SignUpLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div
      className="dark flex min-h-screen items-center justify-center px-4 py-8 text-foreground"
      style={{
        background:
          "radial-gradient(circle at top, color-mix(in srgb, var(--color-sky) 14%, transparent), transparent 38%), var(--background)",
      }}
    >
      {children}
    </div>
  );
}