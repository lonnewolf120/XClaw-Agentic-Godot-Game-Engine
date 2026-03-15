import fs from "fs";
import path from "path";

import { PROJECT_ROOT } from "./commands";

export const GAME_CREATION_MODES = ["standalone", "live_bridge", "project_only"] as const;

export type GameCreationMode = (typeof GAME_CREATION_MODES)[number];

export interface GameRunSummary {
  runId: string;
  prompt: string;
  mode: string;
  status: string;
  retryCount: number;
  validationSummary: string;
  projectDir: string;
  runBundlePath: string;
  createdAtUtc: string;
}

function readJson<T>(filePath: string, fallback: T): T {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf-8")) as T;
  } catch {
    return fallback;
  }
}

function parseRunBundle(bundlePath: string): GameRunSummary | null {
  const payload = readJson<Record<string, unknown>>(bundlePath, {});
  const runId = String(payload.run_id ?? "");
  if (!runId) {
    return null;
  }

  const validation = (payload.validation_report ?? {}) as Record<string, unknown>;
  const state = (payload.state ?? {}) as Record<string, unknown>;

  return {
    runId,
    prompt: String(payload.prompt ?? ""),
    mode: String((state.mode ?? payload.mode) ?? "standalone"),
    status: String(payload.status ?? "unknown"),
    retryCount: Number(payload.retry_count ?? 0),
    validationSummary: String(validation.summary ?? ""),
    projectDir: String(payload.project_dir ?? ""),
    runBundlePath: bundlePath,
    createdAtUtc: String(payload.created_at_utc ?? ""),
  };
}

function listRunBundles(limit = 8): GameRunSummary[] {
  const runsDir = path.join(PROJECT_ROOT, "runs");
  if (!fs.existsSync(runsDir)) {
    return [];
  }

  const bundles = fs
    .readdirSync(runsDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && entry.name.startsWith("run-"))
    .map((entry) => {
      const runDir = path.join(runsDir, entry.name);
      const bundlePath = path.join(runDir, "run_bundle.json");
      const stats = fs.existsSync(bundlePath) ? fs.statSync(bundlePath) : fs.statSync(runDir);
      return {
        bundlePath,
        mtimeMs: stats.mtimeMs,
      };
    })
    .sort((a, b) => b.mtimeMs - a.mtimeMs);

  const summaries: GameRunSummary[] = [];
  for (const item of bundles) {
    if (!fs.existsSync(item.bundlePath)) {
      continue;
    }
    const parsed = parseRunBundle(item.bundlePath);
    if (parsed) {
      summaries.push(parsed);
    }
    if (summaries.length >= limit) {
      break;
    }
  }

  return summaries;
}

export function buildGameCreationSnapshot() {
  const recentRuns = listRunBundles();
  return {
    latestRun: recentRuns[0] ?? null,
    recentRuns,
    availableModes: [...GAME_CREATION_MODES],
  };
}
