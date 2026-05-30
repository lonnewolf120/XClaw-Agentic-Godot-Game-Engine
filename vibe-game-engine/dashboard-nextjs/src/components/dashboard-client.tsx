"use client";

import { useEffect, useMemo, useState } from "react";

type OverviewPayload = {
  timestampUtc: string;
  kpis: {
    benchmarkSuccessRate: number;
    benchmarkTotalPrompts: number;
    needsHumanQueueItems: number;
    triageBatches: number;
  };
  agents: Array<{ name: string; state: "active" | "idle" }>;
  recentRuns: Array<{ runId: string; state: string; path: string }>;
  commands: Array<{ id: string; label: string }>;
};

type JobsPayload = {
  jobs: Array<{
    jobId: string;
    commandId: string;
    status: "running" | "completed" | "failed";
    startedAtUtc: string;
    returnCode?: number;
  }>;
};

const initialOverview: OverviewPayload = {
  timestampUtc: "",
  kpis: {
    benchmarkSuccessRate: 0,
    benchmarkTotalPrompts: 0,
    needsHumanQueueItems: 0,
    triageBatches: 0,
  },
  agents: [],
  recentRuns: [],
  commands: [],
};

export default function DashboardClient() {
  const [overview, setOverview] = useState<OverviewPayload>(initialOverview);
  const [jobs, setJobs] = useState<JobsPayload>({ jobs: [] });
  const [error, setError] = useState("");

  async function refresh() {
    try {
      const [overviewRes, jobsRes] = await Promise.all([fetch("/api/overview"), fetch("/api/jobs")]);
      if (!overviewRes.ok || !jobsRes.ok) throw new Error("Failed to refresh");
      setOverview((await overviewRes.json()) as OverviewPayload);
      setJobs((await jobsRes.json()) as JobsPayload);
      setError("");
    } catch (err) {
      setError(String(err));
    }
  }

  useEffect(() => {
    void refresh();
    const timer = setInterval(() => {
      void refresh();
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  async function runCommand(commandId: string) {
    const res = await fetch("/api/commands/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ commandId }),
    });
    if (!res.ok) {
      setError(`Failed to run command: ${commandId}`);
      return;
    }
    await refresh();
  }

  const benchmarkPercent = useMemo(
    () => `${Math.round((overview.kpis.benchmarkSuccessRate || 0) * 100)}%`,
    [overview.kpis.benchmarkSuccessRate]
  );

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950 px-4 pb-10 text-ink">
      <div className="mx-auto max-w-6xl pt-10">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-amber-300">GENESIS ENGINE Control Plane</p>
        <h1 className="mt-2 font-display text-4xl leading-tight md:text-6xl">Agentic Command Center</h1>
        <p className="mt-3 max-w-3xl text-sm text-muted md:text-base">
          Next.js + Tailwind dashboard for run telemetry, agent visibility, and command execution.
        </p>
        <p className="mt-4 inline-flex items-center gap-2 rounded-full border border-emerald-400/40 px-3 py-1 text-xs text-emerald-300">
          <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-300" />
          {overview.timestampUtc ? `Telemetry synced ${overview.timestampUtc}` : "Syncing telemetry..."}
        </p>
        {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
      </div>

      <div className="mx-auto mt-6 grid max-w-6xl grid-cols-12 gap-4">
        <section className="col-span-12 rounded-xl border border-slate-700 bg-panel/80 p-4 shadow-panel md:col-span-6">
          <h2 className="font-display text-xl">Runtime KPIs</h2>
          <div className="mt-3 grid grid-cols-2 gap-3">
            <KpiCard label="Benchmark Success" value={benchmarkPercent} />
            <KpiCard label="Prompts" value={String(overview.kpis.benchmarkTotalPrompts)} />
            <KpiCard label="Needs-Human Queue" value={String(overview.kpis.needsHumanQueueItems)} />
            <KpiCard label="Triage Batches" value={String(overview.kpis.triageBatches)} />
          </div>
        </section>

        <section className="col-span-12 rounded-xl border border-slate-700 bg-panel/80 p-4 shadow-panel md:col-span-6">
          <h2 className="font-display text-xl">Agent States</h2>
          <div className="mt-3 grid grid-cols-2 gap-3">
            {overview.agents.map((agent) => (
              <article key={agent.name} className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
                <p className="text-sm font-semibold">{agent.name}</p>
                <span
                  className={`mt-2 inline-block rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-[0.12em] ${
                    agent.state === "active"
                      ? "border-emerald-400 text-emerald-300"
                      : "border-slate-500 text-slate-300"
                  }`}
                >
                  {agent.state}
                </span>
              </article>
            ))}
          </div>
        </section>

        <section className="col-span-12 rounded-xl border border-slate-700 bg-panel/80 p-4 shadow-panel">
          <h2 className="font-display text-xl">AI Tools Suite</h2>
          <p className="mt-1 text-sm text-muted">A collection of autonomous development utilities integrated into the engine.</p>
          <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <article className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
              <p className="text-sm font-semibold text-amber-300">2D Sprite Sheet Creator</p>
              <p className="mt-1 text-xs text-slate-400">Generate game-ready pixel characters with walk, jump, and attack animations using text prompts.</p>
              <a
                href="http://localhost:3001"
                target="_blank"
                rel="noreferrer"
                className="mt-3 block w-full rounded-md bg-gradient-to-r from-amber-300 to-orange-400 px-3 flex items-center justify-center py-2 text-xs font-bold uppercase tracking-wide text-slate-900"
              >
                Launch Tool
              </a>
            </article>
          </div>
        </section>

        <section className="col-span-12 rounded-xl border border-slate-700 bg-panel/80 p-4 shadow-panel">
          <h2 className="font-display text-xl">Command Console</h2>
          <p className="mt-1 text-sm text-muted">Trigger allowlisted operations from the dashboard backend API.</p>
          <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {overview.commands.map((cmd) => (
              <article key={cmd.id} className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
                <p className="text-sm font-semibold">{cmd.label}</p>
                <button
                  type="button"
                  onClick={() => void runCommand(cmd.id)}
                  className="mt-3 w-full rounded-md bg-gradient-to-r from-amber-300 to-orange-400 px-3 py-2 text-xs font-bold uppercase tracking-wide text-slate-900"
                >
                  Run
                </button>
              </article>
            ))}
          </div>
        </section>

        <section className="col-span-12 rounded-xl border border-slate-700 bg-panel/80 p-4 shadow-panel md:col-span-7">
          <h2 className="font-display text-xl">Recent Command Jobs</h2>
          <div className="mt-3 space-y-2">
            {jobs.jobs.length === 0 ? (
              <p className="rounded-lg border border-slate-700 bg-slate-900/70 p-3 text-sm text-muted">No jobs yet.</p>
            ) : (
              jobs.jobs.slice(0, 12).map((job) => (
                <article key={job.jobId} className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
                  <p className="text-sm font-semibold">{job.commandId}</p>
                  <p className="mt-1 text-xs text-muted">started: {job.startedAtUtc}</p>
                  <p
                    className={`mt-1 text-xs uppercase tracking-[0.12em] ${
                      job.status === "completed"
                        ? "text-emerald-300"
                        : job.status === "failed"
                          ? "text-rose-300"
                          : "text-amber-300"
                    }`}
                  >
                    {job.status} {job.returnCode !== undefined ? `(code ${job.returnCode})` : ""}
                  </p>
                </article>
              ))
            )}
          </div>
        </section>

        <section className="col-span-12 rounded-xl border border-slate-700 bg-panel/80 p-4 shadow-panel md:col-span-5">
          <h2 className="font-display text-xl">Recent Run Workspaces</h2>
          <div className="mt-3 space-y-2">
            {overview.recentRuns.length === 0 ? (
              <p className="rounded-lg border border-slate-700 bg-slate-900/70 p-3 text-sm text-muted">No runs found.</p>
            ) : (
              overview.recentRuns.map((run) => (
                <article key={run.runId} className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
                  <p className="text-sm font-semibold">{run.runId}</p>
                  <p className="mt-1 text-xs text-muted">{run.state}</p>
                  <p className="mt-1 break-all text-[11px] text-slate-400">{run.path}</p>
                </article>
              ))
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
      <p className="text-[11px] uppercase tracking-[0.12em] text-muted">{label}</p>
      <p className="mt-1 text-2xl font-bold text-amber-300">{value}</p>
    </article>
  );
}
