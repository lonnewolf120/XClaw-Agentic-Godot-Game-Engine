"use client";

import { useMemo, useState } from "react";

import AgentTable from "./sections/agent-table";
import CommandLauncher from "./sections/command-launcher";
import ConfigPanel from "./sections/config-panel";
import EnginePanel from "./sections/engine-panel";
import JobBoard from "./sections/job-board";
import KpiGrid from "./sections/kpi-grid";
import LogTailPanel from "./sections/log-tail-panel";
import RunList from "./sections/run-list";
import ControlPlaneLayout from "./shell/control-plane-layout";
import { useSystemSnapshot } from "./use-system-snapshot";

export type DashboardSection = "overview" | "agents" | "jobs" | "logs" | "engine" | "configs";

const TITLES: Record<DashboardSection, { title: string; description: string }> = {
  overview: {
    title: "Mission Overview",
    description: "Live runtime telemetry, KPIs, and fast command actions",
  },
  agents: {
    title: "Agent Runtime",
    description: "Agent states, roles, and control actions",
  },
  jobs: {
    title: "Job Operations",
    description: "Queue visibility, completion trends, and failures",
  },
  logs: {
    title: "Live Logs",
    description: "Tail and inspect command output in near real-time",
  },
  engine: {
    title: "Engine Health",
    description: "Template, benchmark, and run workspace status",
  },
  configs: {
    title: "Configuration",
    description: "Runtime policy, command allowlist, and environment paths",
  },
};

export default function ControlPlaneSection({ section }: { section: DashboardSection }) {
  const { snapshot, isLoading, error, refresh, activeJobs } = useSystemSnapshot();
  const [runError, setRunError] = useState("");

  async function runCommand(commandId: string) {
    try {
      const response = await fetch("/api/commands/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ commandId }),
      });
      if (!response.ok) {
        throw new Error(`command failed: ${response.status}`);
      }
      setRunError("");
      await refresh();
    } catch (err) {
      setRunError(String(err));
    }
  }

  const benchmarkPercent = useMemo(
    () => `${Math.round((snapshot.overview.kpis.benchmarkSuccessRate || 0) * 100)}%`,
    [snapshot.overview.kpis.benchmarkSuccessRate]
  );

  const frame = TITLES[section];

  return (
    <ControlPlaneLayout
      title={frame.title}
      description={frame.description}
      activeJobs={activeJobs}
      queueItems={snapshot.overview.kpis.needsHumanQueueItems}
      syncedAt={snapshot.timestampUtc}
      error={error}
    >
      {isLoading ? <p className="rounded-lg border border-slate-700 bg-panel/90 p-3 text-sm text-muted">Loading...</p> : null}
      {runError ? <p className="rounded-lg border border-rose-400/40 bg-rose-950/40 p-3 text-sm text-rose-300">{runError}</p> : null}

      {section === "overview" ? (
        <>
          <KpiGrid
            benchmarkSuccess={benchmarkPercent}
            prompts={snapshot.overview.kpis.benchmarkTotalPrompts}
            queue={snapshot.overview.kpis.needsHumanQueueItems}
            triage={snapshot.overview.kpis.triageBatches}
            activeJobs={activeJobs}
          />
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <RunList runs={snapshot.overview.recentRuns} />
            <AgentTable agents={snapshot.overview.agents} />
          </div>
          <CommandLauncher commands={snapshot.overview.commands} onRun={runCommand} />
        </>
      ) : null}

      {section === "agents" ? (
        <>
          <AgentTable agents={snapshot.overview.agents} />
          <CommandLauncher commands={snapshot.overview.commands} onRun={runCommand} />
        </>
      ) : null}

      {section === "jobs" ? <JobBoard jobs={snapshot.jobs} /> : null}

      {section === "logs" ? <LogTailPanel logs={snapshot.logs} /> : null}

      {section === "engine" ? (
        <>
          <EnginePanel engine={snapshot.engine} />
          <RunList runs={snapshot.overview.recentRuns} />
        </>
      ) : null}

      {section === "configs" ? <ConfigPanel configs={snapshot.configs} /> : null}
    </ControlPlaneLayout>
  );
}
