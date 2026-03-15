import fs from "fs";
import path from "path";
import { spawn } from "child_process";
import type { ChildProcess } from "child_process";

import { COMMANDS, PROJECT_ROOT } from "./commands";

export type JobStatus = "running" | "completed" | "failed" | "cancelled";

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

const jobs = new Map<string, CommandJob>();
const runningChildren = new Map<string, ChildProcess>();

function utcNow(): string {
  return new Date().toISOString();
}

export function listJobs(): CommandJob[] {
  return Array.from(jobs.values()).sort((a, b) => b.startedAtUtc.localeCompare(a.startedAtUtc));
}

export function startJob(commandId: string): CommandJob {
  const config = COMMANDS[commandId];
  if (!config) {
    throw new Error("unsupported command");
  }

  return startCustomJob(commandId, config.command, config.cwd);
}

export function startCustomJob(commandId: string, command: string[], cwd: string): CommandJob {
  if (command.length === 0) {
    throw new Error("command must not be empty");
  }

  const job: CommandJob = {
    jobId: `job-${Date.now()}`,
    commandId,
    status: "running",
    startedAtUtc: utcNow(),
  };
  jobs.set(job.jobId, job);

  const logDir = path.join(PROJECT_ROOT, "runs", "dashboard_commands");
  fs.mkdirSync(logDir, { recursive: true });
  const logPath = path.join(logDir, `${job.jobId}.log`);
  job.logPath = logPath;

  const [cmd, ...args] = command;
  const child = spawn(cmd, args, {
    cwd,
    stdio: ["ignore", "pipe", "pipe"],
  });
  runningChildren.set(job.jobId, child);

  const logStream = fs.createWriteStream(logPath, { flags: "w" });
  logStream.write(`[${utcNow()}] START ${commandId}\n${command.join(" ")}\n\n`);
  child.stdout.on("data", (chunk: Buffer) => logStream.write(chunk));
  child.stderr.on("data", (chunk: Buffer) => logStream.write(chunk));

  child.on("close", (code: number | null) => {
    job.endedAtUtc = utcNow();
    const finalCode = code ?? -1;
    job.returnCode = finalCode;
    if (job.status !== "cancelled") {
      job.status = finalCode === 0 ? "completed" : "failed";
    }
    jobs.set(job.jobId, job);
    runningChildren.delete(job.jobId);
    logStream.end();
  });

  return job;
}

export function cancelJob(jobId: string): CommandJob {
  const job = jobs.get(jobId);
  if (!job) {
    throw new Error("job not found");
  }
  if (job.status !== "running") {
    return job;
  }

  const child = runningChildren.get(jobId);
  if (!child) {
    job.status = "failed";
    job.endedAtUtc = utcNow();
    job.returnCode = -1;
    job.message = "process handle missing while cancelling";
    jobs.set(jobId, job);
    return job;
  }

  child.kill("SIGTERM");
  job.status = "cancelled";
  job.endedAtUtc = utcNow();
  job.returnCode = -15;
  job.message = "cancelled by user";
  jobs.set(jobId, job);
  return job;
}
