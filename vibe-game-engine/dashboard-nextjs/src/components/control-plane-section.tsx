"use client";

import { useMemo, useState } from "react";

import AgentTable from "./sections/agent-table";
import CommandLauncher from "./sections/command-launcher";
import ConfigPanel from "./sections/config-panel";
import EnginePanel from "./sections/engine-panel";
import GameExecutionTimelinePanel from "./sections/game-execution-timeline-panel";
import GameBuilderPanel from "./sections/game-builder-panel";
import GameRuntimeControlPanel from "./sections/game-runtime-control-panel";
import GameRunSnapshotPanel from "./sections/game-run-snapshot-panel";
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
  const [createGameLogFile, setCreateGameLogFile] = useState("");

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

  async function createGame(prompt: string, mode: string) {
    try {
      const response = await fetch("/api/game/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, mode }),
      });
      if (!response.ok) {
        throw new Error(`game creation launch failed: ${response.status}`);
      }
      const payload = (await response.json()) as {
        job?: {
          commandId?: string;
          logPath?: string;
        };
      };
      const logPath = payload.job?.logPath;
      if (payload.job?.commandId === "create_game_prompt" && logPath) {
        const normalized = logPath.replace(/\\/g, "/");
        const fileName = normalized.split("/").pop() ?? "";
        setCreateGameLogFile(fileName);
      }
      setRunError("");
      await refresh();
    } catch (err) {
      setRunError(String(err));
      throw err;
    }
  }

  async function cancelGameJob(jobId: string) {
    const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/cancel`, {
      method: "POST",
    });
    if (!response.ok) {
      throw new Error(`cancel failed: ${response.status}`);
    }
    await refresh();
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
          <GameRuntimeControlPanel
            jobs={snapshot.jobs}
            latestRun={snapshot.gameCreation.latestRun}
            onCancel={cancelGameJob}
            onLaunch={createGame}
          />
          <GameBuilderPanel modes={snapshot.gameCreation.availableModes} onCreate={createGame} />
          <GameExecutionTimelinePanel selectedFile={createGameLogFile} />
          <LogTailPanel
            logs={snapshot.logs}
            preferredFile={createGameLogFile}
            title="Game Creation Execution Logs"
          />
          <GameRunSnapshotPanel gameCreation={snapshot.gameCreation} />
          <EnginePanel engine={snapshot.engine} />
          <RunList runs={snapshot.overview.recentRuns} />
        </>
      ) : null}

      {section === "configs" ? <ConfigPanel configs={snapshot.configs} /> : null}
    </ControlPlaneLayout>
  );
}
