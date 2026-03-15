export default function RunList({ runs }: { runs: Array<{ runId: string; state: string; path: string }> }) {
  return (
    <section className="rounded-xl border border-slate-700 bg-panel/90 p-4 shadow-panel">
      <h3 className="font-display text-xl">Recent Runs</h3>
      <div className="mt-3 space-y-2">
        {runs.length === 0 ? (
          <p className="rounded-lg border border-slate-700 bg-slate-900/70 p-3 text-sm text-muted">No runs found.</p>
        ) : (
          runs.map((run) => (
            <article key={run.runId} className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
              <p className="text-sm font-semibold">{run.runId}</p>
              <p className="mt-1 text-xs text-muted">{run.state}</p>
              <p className="mt-1 break-all text-[11px] text-slate-400">{run.path}</p>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
