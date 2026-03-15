import type { SystemSnapshot } from "../../lib/types";

export default function GameRunSnapshotPanel({
  gameCreation,
  onReplay,
}: {
  gameCreation: SystemSnapshot["gameCreation"];
  onReplay?: (prompt: string, mode: string) => void;
}) {
  const latest = gameCreation.latestRun;

  return (
    <section className="rounded-xl border border-slate-700 bg-panel/90 p-4 shadow-panel">
      <h3 className="font-display text-xl">Generated Run Snapshot</h3>
      <p className="mt-1 text-sm text-muted">Inspect the latest prompt-generated project and recent run bundles.</p>

      <div className="mt-3 rounded-lg border border-slate-700 bg-slate-900/70 p-3">
        {latest ? (
          <>
            <p className="text-sm font-semibold">Latest Run: {latest.runId}</p>
            <p className="mt-1 text-xs text-muted">Status: {latest.status}</p>
            <p className="mt-1 text-xs text-muted">Mode: {latest.mode}</p>
            <p className="mt-1 text-xs text-muted">Retries: {latest.retryCount}</p>
            <p className="mt-1 text-xs text-muted">Validation: {latest.validationSummary || "n/a"}</p>
            <p className="mt-1 break-all text-[11px] text-slate-400">Project: {latest.projectDir}</p>
            <p className="mt-1 break-all text-[11px] text-slate-400">Bundle: {latest.runBundlePath}</p>
            
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => onReplay?.(latest.prompt, latest.mode)}
                className="rounded-md border border-amber-300/40 bg-amber-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-amber-200 hover:bg-amber-500/20"
              >
                Replay Prompt
              </button>
              <a
                href={`/api/downloads?runId=${latest.runId}&target=bundle`}
                download
                className="rounded-md border border-emerald-400/40 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-300 hover:bg-emerald-500/20"
              >
                Download Bundle
              </a>
              {latest.status === "completed" && (
                <a
                  href={`/api/downloads?runId=${latest.runId}&target=export`}
                  download
                  className="rounded-md border border-blue-400/40 bg-blue-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-blue-300 hover:bg-blue-500/20"
                >
                  Download .exe
                </a>
              )}
            </div>
          </>
        ) : (
          <p className="text-sm text-muted">No generated run bundles detected yet.</p>
        )}
      </div>

      <div className="mt-3 space-y-2">
        {gameCreation.recentRuns.length === 0 ? (
          <p className="rounded-lg border border-slate-700 bg-slate-900/70 p-3 text-sm text-muted">No recent bundles.</p>
        ) : (
          gameCreation.recentRuns.slice(0, 6).map((run) => (
            <article key={run.runId} className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold">{run.runId}</p>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => onReplay?.(run.prompt, run.mode)}
                    className="text-[10px] uppercase text-amber-300 hover:underline"
                  >
                    Replay
                  </button>
                  <a
                    href={`/api/downloads?runId=${run.runId}&target=bundle`}
                    download
                    className="text-[10px] uppercase text-emerald-300 hover:underline"
                  >
                    Bundle
                  </a>
                </div>
              </div>
              <p className="mt-1 text-xs text-muted">{run.status}</p>
              <p className="mt-1 break-all text-[11px] text-slate-400">{run.projectDir}</p>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
