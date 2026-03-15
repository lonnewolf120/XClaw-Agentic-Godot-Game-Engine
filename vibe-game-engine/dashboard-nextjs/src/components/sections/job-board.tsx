import type { CommandJob } from "../../lib/types";

export default function JobBoard({ jobs }: { jobs: CommandJob[] }) {
  const running = jobs.filter((job) => job.status === "running");
  const completed = jobs.filter((job) => job.status === "completed");
  const failed = jobs.filter((job) => job.status === "failed");
  const cancelled = jobs.filter((job) => job.status === "cancelled");

  return (
    <section className="rounded-xl border border-slate-700 bg-panel/90 p-4 shadow-panel">
      <h3 className="font-display text-xl">Job Board</h3>
      <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-4">
        <JobColumn title={`Running (${running.length})`} jobs={running} />
        <JobColumn title={`Completed (${completed.length})`} jobs={completed.slice(0, 10)} />
        <JobColumn title={`Failed (${failed.length})`} jobs={failed.slice(0, 10)} />
        <JobColumn title={`Cancelled (${cancelled.length})`} jobs={cancelled.slice(0, 10)} />
      </div>
    </section>
  );
}

function JobColumn({ title, jobs }: { title: string; jobs: CommandJob[] }) {
  return (
    <article className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
      <p className="text-sm font-semibold text-amber-200">{title}</p>
      <div className="mt-2 space-y-2">
        {jobs.length === 0 ? (
          <p className="text-xs text-muted">No jobs.</p>
        ) : (
          jobs.map((job) => (
            <div key={job.jobId} className="rounded-md border border-slate-700 bg-slate-950/80 p-2">
              <p className="text-xs font-semibold">{job.commandId}</p>
              <p className="text-[11px] text-muted">{job.startedAtUtc}</p>
              <p className="text-[11px] text-muted">{job.jobId}</p>
              <p className="text-[11px] text-slate-300">
                rc: {job.returnCode === undefined ? "-" : String(job.returnCode)}
              </p>
            </div>
          ))
        )}
      </div>
    </article>
  );
}
