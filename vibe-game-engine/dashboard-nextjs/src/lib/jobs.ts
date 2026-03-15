import fs from "fs";
import path from "path";
import { spawn } from "child_process";

import { COMMANDS, PROJECT_ROOT } from "./commands";

export type JobStatus = "running" | "completed" | "failed";

export interface CommandJob {
  jobId: string;
  commandId: string;
  status: JobStatus;
  startedAtUtc: string;
  endedAtUtc?: string;
  returnCode?: number;
  logPath?: string;
}

const jobs = new Map<string, CommandJob>();

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

  const [cmd, ...args] = config.command;
  const child = spawn(cmd, args, {
    cwd: config.cwd,
    stdio: ["ignore", "pipe", "pipe"],
  });

  const logStream = fs.createWriteStream(logPath, { flags: "w" });
  logStream.write(`[${utcNow()}] START ${commandId}\n${config.command.join(" ")}\n\n`);
  child.stdout.on("data", (chunk: Buffer) => logStream.write(chunk));
  child.stderr.on("data", (chunk: Buffer) => logStream.write(chunk));

  child.on("close", (code: number | null) => {
    job.endedAtUtc = utcNow();
    job.returnCode = code ?? -1;
    job.status = code === 0 ? "completed" : "failed";
    jobs.set(job.jobId, job);
    logStream.end();
  });

  return job;
}
