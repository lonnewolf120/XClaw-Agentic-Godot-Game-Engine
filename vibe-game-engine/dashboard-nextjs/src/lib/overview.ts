import fs from "fs";
import path from "path";

import { COMMANDS, PROJECT_ROOT } from "./commands";
import { listJobs } from "./jobs";

function readJson<T>(filePath: string, fallback: T): T {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf-8")) as T;
  } catch {
    return fallback;
  }
}

function readJsonl(filePath: string): Array<Record<string, unknown>> {
  if (!fs.existsSync(filePath)) return [];
  return fs
    .readFileSync(filePath, "utf-8")
    .split(/\r?\n/)
    .filter((line: string) => line.trim().length > 0)
    .map((line: string) => {
      try {
        return JSON.parse(line) as Record<string, unknown>;
      } catch {
        return {};
      }
    });
}

function recentRuns(limit = 10): Array<{ runId: string; state: string; path: string }> {
  const runsDir = path.join(PROJECT_ROOT, "runs");
  if (!fs.existsSync(runsDir)) return [];

  const dirs = fs
    .readdirSync(runsDir, { withFileTypes: true })
    .filter((entry: fs.Dirent) => entry.isDirectory() && entry.name.startsWith("run-"))
    .map((entry: fs.Dirent) => {
      const fullPath = path.join(runsDir, entry.name);
      const stats = fs.statSync(fullPath);
      return { fullPath, name: entry.name, mtime: stats.mtimeMs };
    })
    .sort((a, b) => b.mtime - a.mtime)
    .slice(0, limit);

  return dirs.map((item) => {
    const escalationTicket = path.join(item.fullPath, ".vibe", "escalation", "needs_human_ticket.json");
    return {
      runId: item.name,
      state: fs.existsSync(escalationTicket) ? "needs_human" : "completed_or_unknown",
      path: item.fullPath,
    };
  });
}

function agentStates(): Array<{ name: string; state: "active" | "idle" }> {
  const runningCommandIds = new Set(
    listJobs()
      .filter((job) => job.status === "running")
      .map((job) => job.commandId)
  );
  return [
    { name: "Project Manager", state: runningCommandIds.has("run_benchmark") ? "active" : "idle" },
    { name: "Coordinator", state: runningCommandIds.has("run_smoke") ? "active" : "idle" },
    { name: "Coding Agent", state: runningCommandIds.has("run_smoke") ? "active" : "idle" },
    { name: "Debugger Agent", state: runningCommandIds.has("run_smoke") ? "active" : "idle" },
    { name: "Exporter Agent", state: "idle" },
    { name: "QA Agent", state: runningCommandIds.has("run_tests") ? "active" : "idle" },
  ];
}

export function buildOverview() {
  const latestBenchmark = readJson<Record<string, unknown>>(
    path.join(PROJECT_ROOT, "benchmarks", "results", "latest.json"),
    {}
  );
  const summary = (latestBenchmark.summary ?? {}) as Record<string, unknown>;
  const queueRows = readJsonl(path.join(PROJECT_ROOT, "runs", "needs_human_queue.jsonl"));
  const triageRows = readJsonl(path.join(PROJECT_ROOT, "runs", "escalation_triage.jsonl"));

  return {
    timestampUtc: new Date().toISOString(),
    kpis: {
      benchmarkSuccessRate: Number(summary.success_rate ?? 0),
      benchmarkTotalPrompts: Number(summary.total_prompts ?? 0),
      needsHumanQueueItems: queueRows.length,
      triageBatches: triageRows.length,
    },
    agents: agentStates(),
    recentRuns: recentRuns(),
    latestBenchmark: summary,
    latestTriage: triageRows.at(-1) ?? {},
    commands: Object.entries(COMMANDS).map(([id, value]) => ({ id, label: value.label })),
  };
}
