"use client";

import { useMemo, useState } from "react";

export default function GameBuilderPanel({
  modes,
  onCreate,
}: {
  modes: string[];
  onCreate: (prompt: string, mode: string) => Promise<void>;
}) {
  const [prompt, setPrompt] = useState("Create a tiny 2D platformer with jump and one enemy");
  const [mode, setMode] = useState("standalone");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const effectiveModes = useMemo(() => (modes.length > 0 ? modes : ["standalone"]), [modes]);

  async function submit() {
    const cleanPrompt = prompt.trim();
    if (!cleanPrompt) {
      setError("Prompt is required");
      return;
    }

    try {
      setIsSubmitting(true);
      setError("");
      await onCreate(cleanPrompt, mode);
    } catch (err) {
      setError(String(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="rounded-xl border border-slate-700 bg-panel/90 p-4 shadow-panel">
      <h3 className="font-display text-xl">Game Builder</h3>
      <p className="mt-1 text-sm text-muted">
        Launch prompt-driven project generation with your new runtime pipeline.
      </p>

      <label className="mt-4 block text-xs uppercase tracking-[0.12em] text-slate-300">Prompt</label>
      <textarea
        value={prompt}
        onChange={(event) => setPrompt(event.target.value)}
        rows={4}
        className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950/80 p-3 text-sm text-slate-100 outline-none ring-amber-300/40 transition focus:ring"
        placeholder="Describe mechanics, constraints, and tone"
      />

      <div className="mt-3 flex flex-wrap items-end gap-3">
        <label className="min-w-48 text-xs uppercase tracking-[0.12em] text-slate-300">
          Run Mode
          <select
            value={mode}
            onChange={(event) => setMode(event.target.value)}
            className="mt-2 block w-full rounded-lg border border-slate-700 bg-slate-950/80 p-2 text-sm text-slate-100"
          >
            {effectiveModes.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          onClick={() => void submit()}
          disabled={isSubmitting}
          className="rounded-md bg-gradient-to-r from-amber-300 to-orange-400 px-4 py-2 text-xs font-bold uppercase tracking-wide text-slate-900 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? "Launching..." : "Create Game"}
        </button>
      </div>

      {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
    </section>
  );
}
