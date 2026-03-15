"use client";

import { X, Box, FileCode, CheckCircle2, CircleDashed, Layers } from "lucide-react";

export function NodeInspector({ onClose }: { onClose: () => void }) {
  return (
    <div className="flex h-full w-full flex-col text-slate-300">
      <div className="flex shrink-0 items-center justify-between border-b border-white/5 px-4 py-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Node Inspector</h3>
        <button onClick={onClose} className="rounded-md p-1 text-slate-500 hover:bg-white/5 hover:text-white transition">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
        <div className="space-y-6">
          {/* Agent Workflow Outline */}
          <div className="space-y-3">
            <h4 className="text-[10px] font-bold uppercase tracking-widest text-slate-500 flex items-center gap-2">
              <div className="h-px flex-1 bg-white/10" />
              Generation Pipeline
              <div className="h-px flex-1 bg-white/10" />
            </h4>
            
            <div className="space-y-2">
              <Step icon={<CheckCircle2 className="text-emerald-500" />} title="Parse Guidelines" time="0.2s" done />
              <Step icon={<CheckCircle2 className="text-emerald-500" />} title="Bootstrap Scene" time="1.4s" done />
              <Step icon={<CircleDashed className="text-amber-500 animate-spin-slow" />} title="Generate GDScript" time="sync..." active />
              <Step icon={<CircleDashed className="text-slate-600" />} title="Headless Verification" />
            </div>
          </div>

          {/* Scene Tree Fake */}
          <div className="space-y-3 pt-4 border-t border-white/5">
            <h4 className="text-[10px] font-bold uppercase tracking-widest text-slate-500 flex items-center gap-2">
              <div className="h-px flex-1 bg-white/10" />
              main.tscn
              <div className="h-px flex-1 bg-white/10" />
            </h4>
            
            <div className="font-mono text-xs space-y-1">
              <TreeNode label="Root (Node3D)" type="root" expanded />
              <TreeNode label="Player (CharacterBody3D)" type="child" indent={1} />
              <TreeNode label="CollisionShape3D" type="leaf" indent={2} />
              <TreeNode label="Camera3D" type="leaf" indent={2} />
              <TreeNode label="Environment (Node3D)" type="child" indent={1} />
              <TreeNode label="DirectionalLight3D" type="leaf" indent={2} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Step({ icon, title, time, done, active }: any) {
  return (
    <div className={`flex items-start gap-3 rounded-lg border p-3 transition ${active ? 'border-amber-500/30 bg-amber-500/5' : done ? 'border-emerald-500/10 bg-emerald-500/5' : 'border-white/5 bg-white/5 opacity-50'}`}>
      <div className="mt-0.5 [&>svg]:h-3.5 [&>svg]:w-3.5">{icon}</div>
      <div className="flex-1">
        <p className={`text-xs font-medium ${active ? 'text-amber-100' : 'text-slate-300'}`}>{title}</p>
      </div>
      {time && <p className="text-[10px] font-mono text-slate-500">{time}</p>}
    </div>
  );
}

function TreeNode({ label, indent = 0, type }: any) {
  return (
    <div 
      className="flex items-center gap-2 py-1 px-2 rounded-sm hover:bg-white/5 cursor-pointer text-slate-400 hover:text-white transition"
      style={{ paddingLeft: `${(indent * 12) + 8}px` }}
    >
      {type === 'root' ? <Layers className="h-3 w-3 text-indigo-400" /> : type === 'child' ? <Box className="h-3 w-3 text-cyan-400" /> : <FileCode className="h-3 w-3 text-amber-600" />}
      <span>{label}</span>
    </div>
  );
}
