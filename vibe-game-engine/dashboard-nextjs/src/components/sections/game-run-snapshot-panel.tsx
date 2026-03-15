import type { SystemSnapshot } from "../../lib/types";

export default function GameRunSnapshotPanel({
  gameCreation,
}: {
  gameCreation: SystemSnapshot["gameCreation"];
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
              <p className="text-sm font-semibold">{run.runId}</p>
              <p className="mt-1 text-xs text-muted">{run.status}</p>
              <p className="mt-1 break-all text-[11px] text-slate-400">{run.projectDir}</p>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
