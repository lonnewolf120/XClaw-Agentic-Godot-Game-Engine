import type { AgentState } from "../../lib/types";

export default function AgentTable({ agents }: { agents: Array<{ name: string; state: AgentState }> }) {
  return (
    <section className="rounded-xl border border-slate-700 bg-panel/90 p-4 shadow-panel">
      <h3 className="font-display text-xl">Agent Registry</h3>
      <div className="mt-3 overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="text-xs uppercase tracking-[0.12em] text-muted">
            <tr>
              <th className="px-2 py-2">Agent</th>
              <th className="px-2 py-2">State</th>
              <th className="px-2 py-2">Role</th>
            </tr>
          </thead>
          <tbody>
            {agents.map((agent) => (
              <tr key={agent.name} className="border-t border-slate-700">
                <td className="px-2 py-2 font-semibold text-slate-100">{agent.name}</td>
                <td className="px-2 py-2">
                  <span
                    className={`rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-[0.12em] ${
                      agent.state === "active"
                        ? "border-emerald-400 text-emerald-300"
                        : "border-slate-500 text-slate-300"
                    }`}
                  >
                    {agent.state}
                  </span>
                </td>
                <td className="px-2 py-2 text-muted">{describeRole(agent.name)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function describeRole(name: string): string {
  if (name.includes("Project Manager")) return "scope and milestone governance";
  if (name.includes("Coordinator")) return "task graph execution";
  if (name.includes("Coding")) return "generation and patching";
  if (name.includes("Debugger")) return "failure diagnosis and recovery";
  if (name.includes("QA")) return "validation and acceptance checks";
  if (name.includes("Exporter")) return "build artifact packaging";
  return "specialized runtime function";
}
