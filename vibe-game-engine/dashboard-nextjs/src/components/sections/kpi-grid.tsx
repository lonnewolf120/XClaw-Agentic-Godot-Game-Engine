export default function KpiGrid({
  benchmarkSuccess,
  prompts,
  queue,
  triage,
  activeJobs,
}: {
  benchmarkSuccess: string;
  prompts: number;
  queue: number;
  triage: number;
  activeJobs: number;
}) {
  return (
    <section className="rounded-xl border border-slate-700 bg-panel/90 p-4 shadow-panel">
      <h3 className="font-display text-xl">Runtime KPIs</h3>
      <div className="mt-3 grid grid-cols-2 gap-3 lg:grid-cols-5">
        <MetricCard label="Benchmark Success" value={benchmarkSuccess} />
        <MetricCard label="Prompts" value={String(prompts)} />
        <MetricCard label="Needs-Human Queue" value={String(queue)} />
        <MetricCard label="Triage Batches" value={String(triage)} />
        <MetricCard label="Active Jobs" value={String(activeJobs)} />
      </div>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
      <p className="text-[11px] uppercase tracking-[0.12em] text-muted">{label}</p>
      <p className="mt-1 text-2xl font-bold text-amber-300">{value}</p>
    </article>
  );
}
