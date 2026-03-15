import type { SystemSnapshot } from "../../lib/types";

export default function NeedsHumanPanel({
  queueItems,
  triageBatches,
  onResolveAll,
}: {
  queueItems: SystemSnapshot["overview"]["queueItems"];
  triageBatches: SystemSnapshot["overview"]["triageBatchesList"];
  onResolveAll?: () => void;
}) {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <section className="rounded-xl border border-rose-900/40 bg-panel/90 p-4 shadow-panel flex flex-col">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-display text-xl text-rose-300">Needs-Human Queue</h3>
            <p className="mt-1 text-sm text-muted">Active runs awaiting manual intervention via triage tool.</p>
          </div>
          {queueItems.length > 0 && onResolveAll && (
            <button
              type="button"
              onClick={onResolveAll}
              className="rounded-md bg-gradient-to-r from-amber-300 to-orange-400 px-3 py-1.5 text-xs font-bold uppercase tracking-wide text-slate-900 hover:opacity-90"
            >
              Resolve Queue
            </button>
          )}
        </div>
        <div className="mt-4 space-y-2 flex-grow overflow-auto max-h-[400px]">
          {queueItems.length === 0 ? (
            <p className="rounded-lg border border-slate-700 bg-slate-900/70 p-3 text-sm text-muted">
              Queue is clear. Nice job.
            </p>
          ) : (
            queueItems.map((item, idx) => (
              <article key={`${item.run_id}-${idx}`} className="rounded-lg border border-rose-900/50 bg-rose-950/20 p-3">
                <p className="text-sm font-semibold">{String(item.run_id ?? "Unknown API Run")}</p>
                <p className="mt-1 text-xs text-rose-300">Reason: {String(item.failure_reason ?? "n/a")}</p>
                <p className="mt-1 text-[11px] text-slate-400">Time: {String(item.timestamp_utc ?? "n/a")}</p>
              </article>
            ))
          )}
        </div>
      </section>

      <section className="rounded-xl border border-slate-700 bg-panel/90 p-4 shadow-panel">
        <h3 className="font-display text-xl text-amber-200">Triage Batches</h3>
        <p className="mt-1 text-sm text-muted">Recently resolved and partially resolved ticket batches.</p>
        <div className="mt-4 space-y-2">
          {triageBatches.length === 0 ? (
            <p className="rounded-lg border border-slate-700 bg-slate-900/70 p-3 text-sm text-muted">
              No triage history found.
            </p>
          ) : (
            triageBatches.slice(-6).reverse().map((batch, idx) => (
              <article key={idx} className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs uppercase tracking-[0.12em] text-amber-200">
                    {String(batch.timestamp_utc ?? "").slice(0, 19).replace("T", " ")}
                  </p>
                  <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] text-slate-300">
                    {Number(batch.resolved ?? 0)} / {Number(batch.batch_size ?? 0)} resolved
                  </span>
                </div>
                <p className="mt-1 text-sm text-muted">
                  Open Tickets: {Number(batch.open_tickets ?? 0)}
                </p>
              </article>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
