"use client";

import { useEffect, useMemo, useState } from "react";

const STAGE_RE = /^\[(.+?)\]\s+\[(.+?)\]\s+(.*)$/;

interface ParsedEvent {
  timestamp: string;
  stage: string;
  message: string;
}

interface LogPayload {
  fileName: string;
  lines: string[];
}

export default function GameExecutionTimelinePanel({ selectedFile }: { selectedFile?: string }) {
  const [events, setEvents] = useState<ParsedEvent[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!selectedFile) return;
    const file = selectedFile;

    async function load() {
      try {
        const response = await fetch(`/api/logs?file=${encodeURIComponent(file)}&maxLines=400`);
        if (!response.ok) {
          throw new Error(`Unable to load log timeline: ${response.status}`);
        }
        const payload = (await response.json()) as LogPayload;
        const parsed = payload.lines
          .map((line) => {
            const match = line.match(STAGE_RE);
            if (!match) return null;
            return {
              timestamp: match[1],
              stage: match[2],
              message: match[3],
            } satisfies ParsedEvent;
          })
          .filter((item): item is ParsedEvent => item !== null);

        setEvents(parsed);
        setError("");
      } catch (err) {
        setError(String(err));
      }
    }

    void load();
    const timer = setInterval(() => {
      void load();
    }, 1500);
    return () => clearInterval(timer);
  }, [selectedFile]);

  const latest = useMemo(() => (events.length > 0 ? events[events.length - 1] : null), [events]);

  return (
    <section className="rounded-xl border border-slate-700 bg-panel/90 p-4 shadow-panel">
      <h3 className="font-display text-xl">Execution Timeline</h3>
      <p className="mt-1 text-sm text-muted">
        Structured real-time stage updates for the current create-game run.
      </p>

      <div className="mt-3 rounded-lg border border-slate-700 bg-slate-900/70 p-3">
        <p className="text-xs uppercase tracking-[0.12em] text-slate-300">Current Stage</p>
        {latest ? (
          <>
            <p className="mt-1 text-sm font-semibold text-amber-200">{latest.stage}</p>
            <p className="mt-1 text-xs text-muted">{latest.message}</p>
            <p className="mt-1 text-[11px] text-slate-400">{latest.timestamp}</p>
          </>
        ) : (
          <p className="mt-2 text-sm text-muted">No stage events yet.</p>
        )}
      </div>

      {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}

      <div className="mt-3 max-h-[320px] space-y-2 overflow-auto pr-1">
        {events.length === 0 ? (
          <p className="rounded-lg border border-slate-700 bg-slate-900/70 p-3 text-sm text-muted">No timeline events.</p>
        ) : (
          events.slice(-30).map((event, index) => (
            <article key={`${event.timestamp}-${event.stage}-${index}`} className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
              <p className="text-[11px] uppercase tracking-[0.12em] text-amber-200">{event.stage}</p>
              <p className="mt-1 text-sm text-slate-100">{event.message}</p>
              <p className="mt-1 text-[11px] text-slate-400">{event.timestamp}</p>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
