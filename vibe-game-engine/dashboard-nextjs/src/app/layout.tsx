import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "GENESIS ENGINE OS Dashboard",
  description: "Full operating dashboard for agent orchestration, logs, jobs, engine state, and configuration.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-ink antialiased">{children}</body>
    </html>
  );
}
