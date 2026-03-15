"use client";

export default function CommandLauncher({
  commands,
  onRun,
}: {
  commands: Array<{ id: string; label: string }>;
  onRun: (commandId: string) => Promise<void>;
}) {
  return (
    <section className="rounded-xl border border-slate-700 bg-panel/90 p-4 shadow-panel">
      <h3 className="font-display text-xl">Command Launcher</h3>
      <p className="mt-1 text-sm text-muted">Trigger allowlisted workflows on the orchestration backend.</p>
      <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
        {commands.map((cmd) => (
          <article key={cmd.id} className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
            <p className="text-sm font-semibold">{cmd.label}</p>
            <button
              type="button"
              onClick={() => void onRun(cmd.id)}
              className="mt-3 w-full rounded-md bg-gradient-to-r from-amber-300 to-orange-400 px-3 py-2 text-xs font-bold uppercase tracking-wide text-slate-900"
            >
              Run
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
