"use client";

import { useMemo, useState } from "react";

import type { CommandJob, GameRunSummary } from "../../lib/types";

export default function GameRuntimeControlPanel({
  jobs,
  latestRun,
  onCancel,
  onLaunch,
}: {
  jobs: CommandJob[];
  latestRun: GameRunSummary | null;
  onCancel: (jobId: string) => Promise<void>;
  onLaunch: (prompt: string, mode: string) => Promise<void>;
}) {
  const activeGameJob = useMemo(
    () => jobs.find((job) => job.commandId === "create_game_prompt" && job.status === "running") ?? null,
    [jobs]
  );

  const [prompt, setPrompt] = useState(
    latestRun?.prompt?.trim() || "Create a tiny 2D platformer with jump and one enemy"
  );
  const [mode, setMode] = useState(latestRun?.mode || "standalone");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function launchNow() {
    const clean = prompt.trim();
    if (!clean) {
      setError("Prompt is required");
      return;
    }
    try {
      setBusy(true);
      setError("");
      await onLaunch(clean, mode);
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  }

  async function cancelNow() {
    if (!activeGameJob) return;
    try {
      setBusy(true);
      setError("");
      await onCancel(activeGameJob.jobId);
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="rounded-xl border border-slate-700 bg-panel/90 p-4 shadow-panel">
      <h3 className="font-display text-xl">Live Runtime Control</h3>
      <p className="mt-1 text-sm text-muted">
        Launch, modify, and cancel active game-generation runs in real time.
      </p>

      <div className="mt-3 rounded-lg border border-slate-700 bg-slate-900/70 p-3">
        <p className="text-xs uppercase tracking-[0.12em] text-slate-300">Active Create Game Job</p>
        {activeGameJob ? (
          <>
            <p className="mt-1 text-sm font-semibold text-amber-200">{activeGameJob.jobId}</p>
            <p className="mt-1 text-xs text-muted">Started: {activeGameJob.startedAtUtc}</p>
            <p className="mt-1 text-xs text-muted">Command: {activeGameJob.commandId}</p>
            <button
              type="button"
              disabled={busy}
              onClick={() => void cancelNow()}
              className="mt-3 rounded-md border border-rose-400/40 bg-rose-500/20 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-rose-200 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Stop Current Run
            </button>
          </>
        ) : (
          <p className="mt-2 text-sm text-emerald-300">No active create-game run.</p>
        )}
      </div>

      <label className="mt-4 block text-xs uppercase tracking-[0.12em] text-slate-300">Editable Prompt</label>
      <textarea
        value={prompt}
        onChange={(event) => setPrompt(event.target.value)}
        rows={4}
        className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950/80 p-3 text-sm text-slate-100 outline-none ring-amber-300/40 transition focus:ring"
      />

      <div className="mt-3 flex flex-wrap items-end gap-3">
        <label className="text-xs uppercase tracking-[0.12em] text-slate-300">
          Mode
          <select
            value={mode}
            onChange={(event) => setMode(event.target.value)}
            className="mt-2 block rounded-lg border border-slate-700 bg-slate-950/80 p-2 text-sm text-slate-100"
          >
            <option value="standalone">standalone</option>
            <option value="live_bridge">live_bridge</option>
            <option value="project_only">project_only</option>
          </select>
        </label>

        <button
          type="button"
          disabled={busy}
          onClick={() => void launchNow()}
          className="rounded-md bg-gradient-to-r from-amber-300 to-orange-400 px-4 py-2 text-xs font-bold uppercase tracking-wide text-slate-900 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Launch / Relaunch
        </button>
      </div>

      {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
    </section>
  );
}
