"use client";

import type { ReactNode } from "react";

import AppNav from "./app-nav";

export default function ControlPlaneLayout({
  title,
  description,
  activeJobs,
  queueItems,
  syncedAt,
  error,
  children,
}: {
  title: string;
  description: string;
  activeJobs: number;
  queueItems: number;
  syncedAt: string;
  error: string;
  children: ReactNode;
}) {
  return (
    <main className="min-h-screen bg-grid px-4 py-5 text-ink md:px-6">
      <div className="mx-auto grid max-w-7xl grid-cols-12 gap-4">
        <aside className="col-span-12 rounded-2xl border border-slate-700/90 bg-panel/90 p-4 shadow-panel md:col-span-3 lg:col-span-2">
          <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-amber-300">Vibe OS</p>
          <h1 className="mt-2 font-display text-2xl">Control Plane</h1>
          <p className="mt-2 text-xs text-muted">Runtime and orchestration command center.</p>
          <div className="mt-4">
            <AppNav />
          </div>
        </aside>

        <section className="col-span-12 space-y-4 md:col-span-9 lg:col-span-10">
          <header className="rounded-2xl border border-slate-700/90 bg-panel/90 p-4 shadow-panel">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-amber-300">{title}</p>
                <h2 className="mt-1 font-display text-3xl">{description}</h2>
              </div>
              <div className="rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-xs text-slate-300">
                <p>Active Jobs: {activeJobs}</p>
                <p>Queue: {queueItems}</p>
                <p>Sync: {syncedAt || "..."}</p>
              </div>
            </div>
            {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
          </header>

          {children}
        </section>
      </div>
    </main>
  );
}
