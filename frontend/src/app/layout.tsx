import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { SidebarProvider } from "@/components/ui/sidebar"
import HideSidebar from "@/components/hide-sidebar"
import { TooltipProvider } from "@/components/ui/tooltip"
import { Toaster } from "@/components/ui/sonner"
import { AppViewProvider } from "@/components/app-view-context"
import { Providers } from "./providers";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Neighbourhood WatchDog",
  description: "Protect your neighbourhood.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${jetbrainsMono.variable} ${inter.variable} h-full`}>
      <body className="min-h-screen flex flex-col">
        <Providers>
          <TooltipProvider>
            <AppViewProvider>
              <SidebarProvider>
                <HideSidebar /> {/*Check if the current layout is allowed to have a sidebar */}
                <main className="flex-1 w-full">
                  {children}
                </main>
              </SidebarProvider>
            </AppViewProvider>
          </TooltipProvider>
          <Toaster position="top-right" />
        </Providers>
      </body>
    </html>
  );
}
