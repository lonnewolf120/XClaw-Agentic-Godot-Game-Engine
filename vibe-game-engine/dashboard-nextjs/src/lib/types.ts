export type AgentState = "active" | "idle";
export type JobStatus = "running" | "completed" | "failed" | "cancelled";

export interface OverviewPayload {
  timestampUtc: string;
  kpis: {
    benchmarkSuccessRate: number;
    benchmarkTotalPrompts: number;
    needsHumanQueueItems: number;
    triageBatches: number;
  };
  agents: Array<{ name: string; state: AgentState }>;
  recentRuns: Array<{ runId: string; state: string; path: string }>;
  commands: Array<{ id: string; label: string }>;
}

export interface CommandJob {
  jobId: string;
  commandId: string;
  status: JobStatus;
  startedAtUtc: string;
  endedAtUtc?: string;
  returnCode?: number;
  logPath?: string;
  message?: string;
}

export interface LogSummary {
  fileName: string;
  path: string;
  sizeBytes: number;
  modifiedUtc: string;
}

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

export interface SystemSnapshot {
  timestampUtc: string;
  overview: OverviewPayload;
  jobs: CommandJob[];
  engine: {
    projectRoot: string;
    templatesCount: number;
    runFoldersCount: number;
    benchmarkResultFiles: number;
    dashboardCommandLogs: number;
    health: {
      templatesPresent: boolean;
      runsPresent: boolean;
      benchmarkPresent: boolean;
    };
  };
  configs: {
    pythonExecutable: string;
    commandAllowlist: Array<{ id: string; label: string; cwd: string; command: string[] }>;
    composeFiles: string[];
  };
  gameCreation: {
    latestRun: GameRunSummary | null;
    recentRuns: GameRunSummary[];
    availableModes: string[];
  };
  logs: LogSummary[];
}
