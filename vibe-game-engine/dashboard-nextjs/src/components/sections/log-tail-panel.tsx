"use client";

import { useEffect, useMemo, useState } from "react";

import type { LogSummary } from "../../lib/types";

interface LogPayload {
  fileName: string;
  lines: string[];
}

export default function LogTailPanel({
  logs,
  preferredFile,
  title = "Log Tail",
}: {
  logs: LogSummary[];
  preferredFile?: string;
  title?: string;
}) {
  const [selectedFile, setSelectedFile] = useState("");
  const [payload, setPayload] = useState<LogPayload | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!selectedFile && logs.length > 0) {
      setSelectedFile(logs[0].fileName);
    }
  }, [logs, selectedFile]);

  useEffect(() => {
    if (!preferredFile) return;
    const exists = logs.some((item) => item.fileName === preferredFile);
    if (exists) {
      setSelectedFile(preferredFile);
    }
  }, [preferredFile, logs]);

  useEffect(() => {
    if (!selectedFile) return;

    async function load() {
      try {
        const response = await fetch(`/api/logs?file=${encodeURIComponent(selectedFile)}&maxLines=180`);
        if (!response.ok) throw new Error(`Unable to load log: ${response.status}`);
        setPayload((await response.json()) as LogPayload);
        setError("");
      } catch (err) {
        setError(String(err));
      }
    }

    void load();
    const timer = setInterval(() => {
      void load();
    }, 2500);

    return () => clearInterval(timer);
  }, [selectedFile]);

  const options = useMemo(
    () => logs.map((log) => ({ value: log.fileName, label: `${log.fileName} (${Math.round(log.sizeBytes / 1024)} KB)` })),
    [logs]
  );

  return (
    <section className="rounded-xl border border-slate-700 bg-panel/90 p-4 shadow-panel">
      <h3 className="font-display text-xl">{title}</h3>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <label className="text-xs uppercase tracking-[0.12em] text-muted">Log file</label>
        <select
          value={selectedFile}
          onChange={(event) => setSelectedFile(event.target.value)}
          className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-sm text-slate-100"
        >
          {options.length === 0 ? <option value="">No logs</option> : null}
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
      <pre className="mt-3 max-h-[420px] overflow-auto rounded-lg border border-slate-700 bg-slate-950/90 p-3 text-xs text-slate-200">
        {(payload?.lines ?? []).join("\n") || "No log output."}
      </pre>
    </section>
  );
}
