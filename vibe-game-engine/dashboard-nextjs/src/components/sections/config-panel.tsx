import type { SystemSnapshot } from "../../lib/types";

export default function ConfigPanel({ configs }: { configs: SystemSnapshot["configs"] }) {
  return (
    <section className="rounded-xl border border-slate-700 bg-panel/90 p-4 shadow-panel">
      <h3 className="font-display text-xl">Configuration Inventory</h3>
      <p className="mt-1 text-sm text-muted">Read-only inventory of command allowlist and runtime paths.</p>

      <div className="mt-3 rounded-lg border border-slate-700 bg-slate-900/70 p-3">
        <p className="text-xs uppercase tracking-[0.12em] text-muted">Python executable</p>
        <p className="mt-1 text-sm text-slate-100">{configs.pythonExecutable}</p>
      </div>

      <div className="mt-3 rounded-lg border border-slate-700 bg-slate-900/70 p-3">
        <p className="text-xs uppercase tracking-[0.12em] text-muted">Command allowlist</p>
        <div className="mt-2 space-y-2">
          {configs.commandAllowlist.map((cmd) => (
            <article key={cmd.id} className="rounded-md border border-slate-700 bg-slate-950/80 p-2 text-xs">
              <p className="font-semibold text-amber-200">{cmd.label}</p>
              <p className="mt-1 text-slate-300">id: {cmd.id}</p>
              <p className="mt-1 break-all text-muted">cwd: {cmd.cwd}</p>
              <p className="mt-1 break-all text-muted">{cmd.command.join(" ")}</p>
            </article>
          ))}
        </div>
      </div>

      <div className="mt-3 rounded-lg border border-slate-700 bg-slate-900/70 p-3">
        <p className="text-xs uppercase tracking-[0.12em] text-muted">Key configuration files</p>
        <ul className="mt-2 space-y-1 text-xs text-slate-300">
          {configs.composeFiles.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
