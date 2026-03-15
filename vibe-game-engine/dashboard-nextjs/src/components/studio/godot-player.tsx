"use client";

import { useEffect, useState, useRef } from "react";
import { Maximize2, RefreshCw, ChevronDown, Activity, AlertTriangle, PlayCircle } from "lucide-react";

export function GodotPlayer({ 
  currentRunId = null, 
  historicalRuns = [] 
}: { 
  currentRunId?: string | null,
  historicalRuns?: {id: string, name: string}[]
}) {
  const [iframeSrc, setIframeSrc] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "building" | "ready" | "failed">("idle");
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    if (currentRunId) {
      setStatus("building");
      // Simulate build channel event
      const timer = setTimeout(() => {
        setIframeSrc(`/exports/${currentRunId}/index.html`);
        setStatus("ready");
      }, 7000); // Updated to match WebSocket completion time (1 + 1.5 + 2 + 1.5 + 0.5) roughly
      return () => clearTimeout(timer);
    } else {
      setStatus("idle");
      setIframeSrc(null);
    }
  }, [currentRunId]);

  const handleRefresh = () => {
    if (iframeRef.current && iframeSrc) {
      iframeRef.current.src = iframeSrc; // force reload
    }
  };

  const toggleFullscreen = () => {
    if (iframeRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        iframeRef.current.requestFullscreen();
      }
    }
  };

  return (
    <div className="relative h-full w-full bg-[#0a0a0a] overflow-hidden group flex flex-col">
      {/* Player Header - Historical Dropdown & Health */}
      <div className="flex justify-between items-center px-4 py-2 bg-[#080d19]/80 backdrop-blur-sm border-b border-white/5 absolute top-0 w-full z-20">
        <div className="flex items-center gap-2">
          <Activity className={`w-3.5 h-3.5 ${status === 'ready' ? 'text-emerald-500' : status === 'failed' ? 'text-red-500' : 'text-amber-500'}`} />
          <span className="text-xs font-mono text-slate-300">
            {status === 'ready' ? 'Live Preview' : status === 'building' ? 'Building...' : status === 'failed' ? 'Build Failed' : 'No Active Build'}
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          {historicalRuns.length > 0 && (
            <div className="flex items-center gap-1 bg-white/5 rounded px-2 py-1 border border-white/5 cursor-pointer hover:bg-white/10 text-xs text-white">
              <span>Past Runs</span>
              <ChevronDown className="w-3 h-3" />
            </div>
          )}
        </div>
      </div>

      {/* Main Viewport */}
      <div className="flex-1 relative top-8 h-[calc(100%-2rem)]">
        {status === "ready" && iframeSrc ? (
          <iframe 
            ref={iframeRef}
            title="Godot Web Export" 
            src={iframeSrc} 
            className="w-full h-full border-none"
            allow="fullscreen"
          />
        ) : status === "failed" ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/50">
            <AlertTriangle className="w-8 h-8 text-red-500 mb-2" />
            <p className="text-slate-400 font-mono text-xs">Preview unavailable. Check logs.</p>
          </div>
        ) : status === "idle" ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <PlayCircle className="h-16 w-16 mb-4 text-white/5" />
            <p className="text-slate-400 font-mono text-xs opacity-70">Awaiting Game Prompt...</p>
          </div>
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="h-16 w-16 mb-4 rounded-full border border-white/5 border-t-amber-500 animate-spin" />
            <p className="text-slate-400 font-mono text-xs opacity-70 animate-pulse">
              Awaiting Build Output...
            </p>
          </div>
        )}
      </div>
      
      {/* Overlay Controls */}
      <div className="absolute bottom-4 right-4 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-20">
        <button 
          onClick={handleRefresh}
          className="p-2 rounded-lg bg-black/60 text-slate-300 hover:text-white backdrop-blur border border-white/10 hover:bg-white/10 transition shadow-lg"
          title="Refresh Preview"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
        <button 
          onClick={toggleFullscreen}
          className="p-2 rounded-lg bg-black/60 text-slate-300 hover:text-white backdrop-blur border border-white/10 hover:bg-white/10 transition shadow-lg"
          title="Fullscreen"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
