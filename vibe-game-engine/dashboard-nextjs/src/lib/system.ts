import fs from "fs";
import path from "path";

import { COMMANDS, PROJECT_ROOT } from "./commands";
import { listJobs } from "./jobs";
import { buildOverview } from "./overview";

export interface LogSummary {
  fileName: string;
  path: string;
  sizeBytes: number;
  modifiedUtc: string;
}

function safeCountDirs(dirPath: string): number {
  try {
    return fs.readdirSync(dirPath, { withFileTypes: true }).filter((entry) => entry.isDirectory()).length;
  } catch {
    return 0;
  }
}

function safeCountFiles(dirPath: string, extension?: string): number {
  try {
    return fs
      .readdirSync(dirPath, { withFileTypes: true })
      .filter((entry) => entry.isFile() && (!extension || entry.name.endsWith(extension))).length;
  } catch {
    return 0;
  }
}

function readTail(filePath: string, maxLines: number): string[] {
  try {
    const content = fs.readFileSync(filePath, "utf-8");
    return content.split(/\r?\n/).slice(-maxLines);
  } catch {
    return [];
  }
}

export function listRecentLogs(limit = 12): LogSummary[] {
  const logDir = path.join(PROJECT_ROOT, "runs", "dashboard_commands");
  if (!fs.existsSync(logDir)) return [];

  return fs
    .readdirSync(logDir, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith(".log"))
    .map((entry) => {
      const filePath = path.join(logDir, entry.name);
      const stats = fs.statSync(filePath);
      return {
        fileName: entry.name,
        path: filePath,
        sizeBytes: stats.size,
        modifiedUtc: new Date(stats.mtimeMs).toISOString(),
      };
    })
    .sort((a, b) => b.modifiedUtc.localeCompare(a.modifiedUtc))
    .slice(0, limit);
}

export function readLogByName(fileName: string, maxLines = 200): { fileName: string; lines: string[] } | null {
  const cleanName = path.basename(fileName);
  if (!cleanName.endsWith(".log")) return null;
  const fullPath = path.join(PROJECT_ROOT, "runs", "dashboard_commands", cleanName);
  if (!fs.existsSync(fullPath)) return null;

  return {
    fileName: cleanName,
    lines: readTail(fullPath, maxLines),
  };
}

export function buildSystemSnapshot() {
  const overview = buildOverview();
  const jobs = listJobs();
  const logs = listRecentLogs();

  const templatesDir = path.join(PROJECT_ROOT, "templates");
  const runsDir = path.join(PROJECT_ROOT, "runs");
  const benchmarkDir = path.join(PROJECT_ROOT, "benchmarks", "results");

  return {
    timestampUtc: new Date().toISOString(),
    overview,
    jobs,
    engine: {
      projectRoot: PROJECT_ROOT,
      templatesCount: safeCountDirs(templatesDir),
      runFoldersCount: safeCountDirs(runsDir),
      benchmarkResultFiles: safeCountFiles(benchmarkDir, ".json"),
      dashboardCommandLogs: logs.length,
      health: {
        templatesPresent: fs.existsSync(templatesDir),
        runsPresent: fs.existsSync(runsDir),
        benchmarkPresent: fs.existsSync(benchmarkDir),
      },
    },
    configs: {
      pythonExecutable: process.env.PYTHON || "python",
      commandAllowlist: Object.entries(COMMANDS).map(([id, value]) => ({
        id,
        label: value.label,
        cwd: value.cwd,
        command: value.command,
      })),
      composeFiles: [
        "docker-compose.vibe-baseline.yml",
        "docker-godot-headless/godot4/Dockerfile",
        "PROJECT_MANAGEMENT/MASTER_PLAN.md",
      ],
    },
    logs,
  };
}
