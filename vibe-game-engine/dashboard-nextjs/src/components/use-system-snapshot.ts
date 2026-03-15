"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import type { SystemSnapshot } from "../lib/types";

const EMPTY: SystemSnapshot = {
  timestampUtc: "",
  overview: {
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
  },
  jobs: [],
  engine: {
    projectRoot: "",
    templatesCount: 0,
    runFoldersCount: 0,
    benchmarkResultFiles: 0,
    dashboardCommandLogs: 0,
    health: {
      templatesPresent: false,
      runsPresent: false,
      benchmarkPresent: false,
    },
  },
  configs: {
    pythonExecutable: "python",
    commandAllowlist: [],
    composeFiles: [],
  },
  logs: [],
};

export function useSystemSnapshot() {
  const [snapshot, setSnapshot] = useState<SystemSnapshot>(EMPTY);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const response = await fetch("/api/system");
      if (!response.ok) {
        throw new Error(`Snapshot request failed: ${response.status}`);
      }
      setSnapshot((await response.json()) as SystemSnapshot);
      setError("");
    } catch (err) {
      setError(String(err));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = setInterval(() => {
      void refresh();
    }, 3000);
    return () => clearInterval(timer);
  }, [refresh]);

  const activeJobs = useMemo(
    () => snapshot.jobs.filter((job) => job.status === "running").length,
    [snapshot.jobs]
  );

  return {
    snapshot,
    isLoading,
    error,
    refresh,
    activeJobs,
  };
}
