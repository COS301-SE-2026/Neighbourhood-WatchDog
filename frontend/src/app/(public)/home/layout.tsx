import { ReactNode } from "react";

export default function HomeLayout({ children }: { children: ReactNode }) {
  return (
    <div className="dark min-h-screen flex flex-col !bg-background text-foreground">
      {children}
    </div>
  )
}