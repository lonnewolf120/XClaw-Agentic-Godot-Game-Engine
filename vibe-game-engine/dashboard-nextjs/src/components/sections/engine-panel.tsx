import type { SystemSnapshot } from "../../lib/types";

export default function EnginePanel({ engine }: { engine: SystemSnapshot["engine"] }) {
  return (
    <section className="rounded-xl border border-slate-700 bg-panel/90 p-4 shadow-panel">
      <h3 className="font-display text-xl">Engine State</h3>
      <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4">
        <EngineCard label="Templates" value={engine.templatesCount} ok={engine.health.templatesPresent} />
        <EngineCard label="Run Folders" value={engine.runFoldersCount} ok={engine.health.runsPresent} />
        <EngineCard label="Benchmark Files" value={engine.benchmarkResultFiles} ok={engine.health.benchmarkPresent} />
        <EngineCard label="Dashboard Logs" value={engine.dashboardCommandLogs} ok={engine.dashboardCommandLogs > 0} />
      </div>
      <p className="mt-3 text-xs text-muted">Project root: {engine.projectRoot}</p>
    </section>
  );
}

function EngineCard({ label, value, ok }: { label: string; value: number; ok: boolean }) {
  return (
    <article className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
      <p className="text-[11px] uppercase tracking-[0.12em] text-muted">{label}</p>
      <p className="mt-1 text-2xl font-bold text-amber-300">{value}</p>
      <p className={`mt-2 text-[11px] uppercase tracking-[0.12em] ${ok ? "text-emerald-300" : "text-rose-300"}`}>
        {ok ? "Healthy" : "Needs attention"}
      </p>
    </article>
  );
}
