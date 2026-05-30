"use client";

import { X, Search, Filter } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

type ActivityEvent = {
  timestamp: string;
  level: string;
  source: string;
  event_type: string;
  message: string;
  details: Record<string, unknown>;
};

export function ConsoleDock({ onClose }: { onClose: () => void }) {
  const [tab, setTab] = useState("logs");
  const [filter, setFilter] = useState("");
  const [events, setEvents] = useState<ActivityEvent[]>([]);

  useEffect(() => {
    let mounted = true;

    const fetchEvents = async () => {
      try {
        const source = tab === "godot" ? "plugin_bridge" : tab === "terminal" ? "backend" : "";
        const query = new URLSearchParams({ limit: "250" });
        if (source) query.set("source", source);
        const res = await fetch(`${BACKEND_URL}/api/v1/activities?${query.toString()}`, { cache: "no-store" });
        if (!res.ok) return;
        const data = await res.json();
        if (mounted) {
          setEvents(Array.isArray(data.events) ? data.events : []);
        }
      } catch {
        // Keep stale events if polling fails.
      }
    };

    fetchEvents();
    const interval = setInterval(fetchEvents, 2000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [tab]);

  const filteredEvents = useMemo(() => {
    if (!filter.trim()) return events;
    const q = filter.toLowerCase();
    return events.filter((e) => {
      const detailsText = JSON.stringify(e.details || {}).toLowerCase();
      return (
        e.message.toLowerCase().includes(q) ||
        e.source.toLowerCase().includes(q) ||
        e.event_type.toLowerCase().includes(q) ||
        detailsText.includes(q)
      );
    });
  }, [events, filter]);

  return (
    <div className="flex h-full w-full flex-col font-mono text-sm shadow-[inset_0_1px_rgba(255,255,255,0.1)] custom-scrollbar">
      <div className="flex h-10 shrink-0 items-center justify-between border-b border-white/5 bg-[#0a0f1a] px-2">
        <div className="flex h-full items-center">
          <TabButton active={tab === "logs"} onClick={() => setTab("logs")}>Agent Logs</TabButton>
          <TabButton active={tab === "godot"} onClick={() => setTab("godot")}>Godot Engine Output</TabButton>
          <TabButton active={tab === "terminal"} onClick={() => setTab("terminal")}>Terminal</TabButton>
        </div>
        
        <div className="flex items-center gap-2 pr-2">
          <div className="flex items-center rounded bg-black/40 px-2 py-1 border border-white/5">
            <Search className="h-3 w-3 text-slate-500 mr-2" />
            <input 
              type="text" 
              placeholder="Filter logs..." 
              className="bg-transparent text-xs text-white placeholder-slate-600 outline-none w-40"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
          </div>
          <button className="p-1.5 rounded hover:bg-white/10 text-slate-400 transition ml-1">
            <Filter className="h-3 w-3" />
          </button>
          <div className="w-px h-4 bg-white/10 mx-1" />
          <button onClick={onClose} className="p-1.5 rounded hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition">
            <X className="h-3 w-3" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto bg-[#03050a] p-3 space-y-1 text-xs text-slate-400 font-mono pb-8">
        {filteredEvents.length === 0 ? (
          <div className="flex items-center gap-2 mt-2">
            <span className="text-amber-500 animate-pulse">█</span>
            <span className="text-slate-500">Waiting for live activity stream...</span>
          </div>
        ) : (
          filteredEvents.map((ev, idx) => {
            const dt = new Date(ev.timestamp);
            const time = Number.isNaN(dt.getTime())
              ? "--:--:--"
              : dt.toLocaleTimeString([], { hour12: false });
            return (
              <LogLine
                key={`${ev.timestamp}-${idx}`}
                time={time}
                level={normalizeLevel(ev.level)}
                msg={`${ev.source}/${ev.event_type}: ${ev.message}${formatDetails(ev.details)}`}
              />
            );
          })
        )}
      </div>
    </div>
  );
}

function normalizeLevel(level: string): "info" | "warn" | "error" | "success" | "system" {
  const lower = (level || "").toLowerCase();
  if (lower === "error") return "error";
  if (lower === "warn" || lower === "warning") return "warn";
  if (lower === "success") return "success";
  if (lower === "system") return "system";
  return "info";
}

function formatDetails(details: Record<string, unknown>): string {
  if (!details || Object.keys(details).length === 0) return "";
  const text = JSON.stringify(details);
  if (text.length <= 160) return ` | ${text}`;
  return ` | ${text.slice(0, 157)}...`;
}

function TabButton({ children, active, onClick }: { children: React.ReactNode, active: boolean, onClick: () => void }) {
  return (
    <button 
      onClick={onClick}
      className={`relative flex h-full items-center px-4 text-xs font-medium transition-colors ${active ? 'text-white' : 'text-slate-500 hover:text-slate-300'}`}
    >
      {children}
      {active && <span className="absolute bottom-0 left-0 h-0.5 w-full bg-amber-500 rounded-t-full shadow-[0_0_10px_rgba(245,158,11,0.5)]" />}
    </button>
  );
}

function LogLine({ time, level, msg }: any) {
  const colors = {
    info: "text-slate-400",
    warn: "text-amber-400",
    error: "text-rose-400",
    success: "text-emerald-400",
    system: "text-indigo-400",
  };
  return (
    <div className="flex gap-3 hover:bg-white/5 py-0.5 px-2 rounded-sm group font-mono">
      <span className="text-slate-600 w-16 shrink-0">{time}</span>
      <span className={`w-20 shrink-0 capitalize ${(colors as any)[level]}`}>[{level}]</span>
      <span className="text-slate-300 group-hover:text-white break-all">{msg}</span>
    </div>
  );
}
