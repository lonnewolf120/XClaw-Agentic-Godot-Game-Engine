"use client";

import { Mic, Paperclip, SendHorizonal, Shapes, Loader2 } from "lucide-react";
import { useState } from "react";

const GAME_PRESETS = ["3D Platformer", "FPS Controller", "City Builder", "Top-Down Racing"];
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

type ExecutionMode = "dashboard_run" | "plugin_delegate";
type ProviderMode = "gemini" | "gemini_cli" | "copilot_cli" | "codex_cli";

export function PromptInterface({ onRunStart }: { onRunStart?: (runId: string) => void }) {
  const [focused, setFocused] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationLogs, setGenerationLogs] = useState<string[]>([]);
  const [executionMode, setExecutionMode] = useState<ExecutionMode>("plugin_delegate");
  const [providerMode, setProviderMode] = useState<ProviderMode>("gemini");
  const [modelName, setModelName] = useState("gemini-3.1-pro-preview");

  const handlePreset = (preset: string) => {
    setPrompt(`Create a ${preset} where I can `);
    setFocused(true);
  };

  const handleGenerate = async () => {
    if (!prompt.trim() || isGenerating) return;
    setIsGenerating(true);
    setGenerationLogs([]);

    try {
      if (executionMode === "plugin_delegate") {
        setGenerationLogs(["[Dashboard] Requesting proposal from backend..."]);
        const proposalRes = await fetch(`${BACKEND_URL}/plugin/proposal`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            prompt,
            selection: [],
            mode: "scene_mutation",
            llm_provider: providerMode,
            llm_model: modelName,
            options: {
              llm_provider: providerMode,
              llm_model: modelName,
            },
          }),
        });

        const proposalData = await proposalRes.json();
        if (!proposalRes.ok) {
          throw new Error(proposalData?.detail || "Failed to create proposal");
        }

        setGenerationLogs((prev) => [
          ...prev,
          `[Dashboard] Proposal created: ${proposalData.proposal_id}`,
          `[Dashboard] Enqueuing proposal for plugin polling...`,
        ]);

        const enqueueRes = await fetch(`${BACKEND_URL}/plugin/enqueue_proposal`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...proposalData,
            source: "dashboard-nextjs",
            delegated_at: new Date().toISOString(),
          }),
        });

        const enqueueData = await enqueueRes.json();
        if (!enqueueRes.ok) {
          throw new Error(enqueueData?.detail || "Failed to enqueue proposal");
        }

        setGenerationLogs((prev) => [
          ...prev,
          `[Dashboard] Enqueued. Queue length: ${enqueueData.queue_length ?? "unknown"}`,
          `[Dashboard] Waiting for plugin Auto-Poll to pick this up.`,
        ]);
        setIsGenerating(false);
        return;
      }

      // Legacy dashboard-run mode
      const res = await fetch(`${BACKEND_URL}/api/v1/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();

      if (data.run_id) {
        if (onRunStart) {
          onRunStart(data.run_id);
        }
        const wsBase = BACKEND_URL.replace(/^http/i, "ws");
        const ws = new WebSocket(`${wsBase}/api/v1/ws/${data.run_id}`);
        
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
      setGenerationLogs((prev) => [...prev, `[Dashboard] Error: ${(err as Error).message}`]);
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
                <select
                  value={executionMode}
                  onChange={(e) => setExecutionMode(e.target.value as ExecutionMode)}
                  className="rounded bg-white/5 border border-white/10 text-[10px] uppercase font-mono tracking-wider text-slate-300 px-2 py-1"
                  disabled={isGenerating}
                >
                  <option value="plugin_delegate">Delegate to Plugin</option>
                  <option value="dashboard_run">Dashboard Run</option>
                </select>
                <select
                  value={providerMode}
                  onChange={(e) => setProviderMode(e.target.value as ProviderMode)}
                  className="rounded bg-white/5 border border-white/10 text-[10px] uppercase font-mono tracking-wider text-slate-300 px-2 py-1"
                  disabled={isGenerating || executionMode !== "plugin_delegate"}
                >
                  <option value="gemini">Gemini</option>
                  <option value="gemini_cli">Gemini CLI</option>
                  <option value="copilot_cli">Copilot CLI</option>
                  <option value="codex_cli">Codex CLI</option>
                </select>
                <input
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  disabled={isGenerating || executionMode !== "plugin_delegate"}
                  className="w-44 rounded bg-white/5 border border-white/10 text-[10px] font-mono tracking-wider text-slate-200 px-2 py-1"
                  placeholder="Model"
                />
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
