"use client";

import { Mic, Paperclip, SendHorizonal, Shapes, Loader2 } from "lucide-react";
import { useState } from "react";

const GAME_PRESETS = ["3D Platformer", "FPS Controller", "City Builder", "Top-Down Racing"];

export function PromptInterface({ onRunStart }: { onRunStart?: (runId: string) => void }) {
  const [focused, setFocused] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationLogs, setGenerationLogs] = useState<string[]>([]);

  const handlePreset = (preset: string) => {
    setPrompt(`Create a ${preset} where I can `);
    setFocused(true);
  };

  const handleGenerate = async () => {
    if (!prompt.trim() || isGenerating) return;
    setIsGenerating(true);
    setGenerationLogs([]);

    try {
      // 1. Trigger API
      const res = await fetch("http://localhost:8000/api/v1/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();

      if (data.run_id) {
        if (onRunStart) {
          onRunStart(data.run_id);
        }
        // 2. Connect WebSocket to stream logs seamlessly
        const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/${data.run_id}`);
        
        ws.onmessage = (event) => {
          const msg = JSON.parse(event.data);
          if (msg.type === "log") {
            setGenerationLogs(prev => [...prev, msg.data]);
            console.log(msg.data); // Would usually dispatch to a context/store
          } else if (msg.type === "success") {
            setIsGenerating(false);
            ws.close();
            // Trigger UI update to switch to viewport/ready state
          }
        };

        ws.onerror = () => {
          setIsGenerating(false);
          ws.close();
        };
      }
    } catch (err) {
      console.error(err);
      setIsGenerating(false);
    }
  };

  return (
    <div className="flex flex-col gap-2 w-full">
      {/* Preset Chips */}
      <div className="flex flex-wrap gap-2 px-2">
        {GAME_PRESETS.map((preset) => (
          <button 
            key={preset}
            onClick={() => handlePreset(preset)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 hover:border-amber-500/30 text-[10px] uppercase font-mono tracking-widest text-slate-400 hover:text-amber-300 transition-colors"
          >
            <Shapes className="w-3 h-3" />
            {preset}
          </button>
        ))}
      </div>

      {/* Main Bar */}
      <div className={`relative w-full rounded-2xl bg-[#111827]/80 backdrop-blur-xl border transition-all duration-300 ${focused ? 'border-amber-500/50 shadow-[0_0_30px_-5px_rgba(245,158,11,0.2)]' : 'border-white/10 shadow-lg'}`}>
        <div className="flex flex-col w-full">
          <textarea 
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder="Describe your game. e.g. 'Create a 3D racing game where I drive a red buggy on a desert track...'"
            className="w-full resize-none bg-transparent p-4 text-sm text-white placeholder-slate-500 focus:outline-none min-h-[80px]"
            disabled={isGenerating}
          />
          
          <div className="flex items-center justify-between px-3 pb-3">
            <div className="flex items-center gap-1">
              <button className="rounded p-2 text-slate-400 hover:bg-white/5 hover:text-white transition group relative">
                <Paperclip className="h-4 w-4" />
              </button>
              <button className="rounded p-2 text-slate-400 hover:bg-white/5 hover:text-white transition">
                <Mic className="h-4 w-4" />
              </button>
              <div className="h-4 w-px bg-white/10 mx-1" />
              <span className="text-[10px] uppercase font-mono tracking-widest text-slate-500 ml-2">Base Control Mode</span>
            </div>

            <button 
              onClick={handleGenerate}
              disabled={isGenerating}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold shadow-md transition-all active:scale-95 ${isGenerating ? 'bg-amber-500/50 text-amber-900 cursor-not-allowed' : 'bg-amber-500 text-amber-950 hover:bg-amber-400'}`}
            >
              {isGenerating ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  WORKING...
                </>
              ) : (
                <>
                  GENERATE
                  <SendHorizonal className="h-3.5 w-3.5" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
      
      {/* Temporary log overlay to show API connection success visually */}
      {isGenerating && generationLogs.length > 0 && (
         <div className="absolute -top-16 left-0 right-0 bg-black/80 rounded border border-white/10 p-2 font-mono text-[10px] text-emerald-400 opacity-80 backdrop-blur-md">
            {generationLogs[generationLogs.length - 1]}
         </div>
      )}
    </div>
  );
}
