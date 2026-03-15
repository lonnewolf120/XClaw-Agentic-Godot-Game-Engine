"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Play, 
  Terminal, 
  Settings, 
  Layers, 
  Hammer, 
  Sparkles,
  PanelRight,
  PanelBottom,
  Download,
  MoreHorizontal,
  Bot
} from "lucide-react";
import { cn } from "../../lib/utils";

// Sub-components (These could be broken out, but keeping here for speed)
import { GodotPlayer } from "./godot-player";
import { PromptInterface } from "./prompt-interface";
import { NodeInspector } from "./node-inspector";
import { ConsoleDock } from "./console-dock";
import { EditorPanel } from "./editor-panel";
import { DiffPanel } from "./diff-panel";
import { ShareDialog } from "./share-dialog";
import { ServiceStatus } from "./service-status";

export function StudioLayout() {
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(true);
  const [isBottomPanelOpen, setIsBottomPanelOpen] = useState(true);
  const [activeTab, setActiveTab] = useState<"viewport" | "code" | "diff">("viewport");
  const [isShareOpen, setIsShareOpen] = useState(false);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);

  const handleRunStart = (runId: string) => {
    setActiveRunId(runId);
  };

  return (
    <div className="flex h-screen w-full flex-col bg-[#050914] text-slate-300 font-sans overflow-hidden selection:bg-amber-500/30">
      {/* Top Header */}
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-white/5 px-4 bg-[#080d19]/80 backdrop-blur-md z-10 relative">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
              <Bot className="h-4 w-4" />
            </div>
            <div className="flex flex-col">
              <h1 className="text-sm font-bold text-white leading-tight font-display tracking-wide">VIBE ENGINE <span className="text-amber-500/80">3D</span></h1>
              <span className="text-[10px] text-slate-500 font-mono">MVP BUILD .02</span>
            </div>
          </div>
          
          <div className="h-6 w-px bg-white/10 mx-2" />
          
          <div className="flex items-center gap-1 rounded-md bg-white/5 p-1 border border-white/5">
            <button 
              onClick={() => setActiveTab("viewport")}
              className={cn("px-3 py-1 text-xs font-medium rounded-sm transition-all duration-200", activeTab === "viewport" ? "bg-white/10 text-white shadow-sm" : "text-slate-400 hover:text-white")}
            >
              Viewport
            </button>
            <button 
              onClick={() => setActiveTab("code")}
              className={cn("px-3 py-1 text-xs font-medium rounded-sm transition-all duration-200", activeTab === "code" ? "bg-white/10 text-white shadow-sm" : "text-slate-400 hover:text-white")}
            >
              Code Editor
            </button>
            <button 
              onClick={() => setActiveTab("diff")}
              className={cn("px-3 py-1 text-xs font-medium rounded-sm transition-all duration-200", activeTab === "diff" ? "bg-white/10 text-white shadow-sm" : "text-slate-400 hover:text-white")}
            >
              Changes
            </button>
          </div>

        </div>

        <div className="flex items-center gap-3">
          {/* Active Services Indicators */}
          <ServiceStatus />

          <button 
            onClick={() => setIsShareOpen(true)}
            className="flex items-center gap-2 rounded-md bg-white/5 hover:bg-white/10 px-3 py-1.5 text-xs font-medium transition-colors text-white border border-white/10 ml-2"
          >
            <Download className="h-3 w-3" />
            Share / Export
          </button>
          <button className="flex items-center gap-2 rounded-md bg-amber-500 hover:bg-amber-400 px-4 py-1.5 text-xs font-bold transition-all text-amber-950 shadow-[0_0_15px_-3px_rgba(245,158,11,0.4)]">
            <Play className="h-3.5 w-3.5 fill-amber-950" />
            Run Build
          </button>
        </div>
      </header>

      {/* Main Workspace */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Toolbar */}
        <aside className="w-12 shrink-0 flex flex-col items-center border-r border-white/5 bg-[#080d19]/50 py-4 gap-4 z-10">
          <ToolButton icon={<Layers />} label="Scene" active />
          <ToolButton icon={<Hammer />} label="Build" />
          <div className="h-px w-6 bg-white/10 my-2" />
          <ToolButton 
            icon={<PanelBottom />} 
            label="Toggle Console" 
            onClick={() => setIsBottomPanelOpen(!isBottomPanelOpen)}
            active={isBottomPanelOpen}
          />
          <ToolButton 
            icon={<PanelRight />} 
            label="Toggle Inspector" 
            onClick={() => setIsRightPanelOpen(!isRightPanelOpen)}
            active={isRightPanelOpen}
          />
          <div className="flex-1" />
          <ToolButton icon={<Settings />} label="Engine Config" />
        </aside>

        {/* Center Canvas & Bottom Dock */}
        <div className="flex flex-1 flex-col overflow-hidden relative">
          
          <main className="flex-1 relative bg-[radial-gradient(ellipse_at_center,rgba(255,255,255,0.03)_0%,transparent_100%)] p-2">
            {/* Background Grid Pattern */}
            <div className="absolute inset-0 max-w-full overflow-hidden pointer-events-none z-0 mix-blend-screen opacity-30 dashboard-bg-grid" />
            
            <div className="h-full w-full rounded-xl border border-white/10 bg-black/40 shadow-2xl relative overflow-hidden flex items-center justify-center z-10">
                <AnimatePresence mode="wait">
                  {activeTab === "viewport" ? (
                    <motion.div 
                      key="viewport"
                      initial={{ opacity: 0, scale: 0.98 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.98 }}
                      className="absolute inset-0"
                    >
                      <GodotPlayer currentRunId={activeRunId} />
                    </motion.div>
                  ) : activeTab === "code" ? (
                    <motion.div 
                      key="code"
                      initial={{ opacity: 0, scale: 0.98 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.98 }}
                      className="w-full h-full text-sm text-amber-200/70 overflow-hidden bg-transparent"
                    >
                      <EditorPanel 
                        fileName="res://scripts/player.gd"
                        fileContent={`extends CharacterBody3D

const SPEED = 5.0
const JUMP_VELOCITY = 4.5
var gravity = ProjectSettings.get_setting("physics/3d/default_gravity")

func _physics_process(delta):
    if not is_on_floor():
        velocity.y -= gravity * delta

    if Input.is_action_just_pressed("ui_accept") and is_on_floor():
        velocity.y = JUMP_VELOCITY

    var input_dir = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
    var direction = (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
    if direction:
        velocity.x = direction.x * SPEED
        velocity.z = direction.z * SPEED
    else:
        velocity.x = move_toward(velocity.x, 0, SPEED)
        velocity.z = move_toward(velocity.z, 0, SPEED)

    move_and_slide()`}
                      />
                    </motion.div>
                  ) : (
                    <motion.div 
                      key="diff"
                      initial={{ opacity: 0, scale: 0.98 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.98 }}
                      className="w-full h-full text-sm overflow-hidden bg-transparent"
                    >
                      <DiffPanel 
                        files={[
                          { path: 'res://scripts/player.gd', added: 12, deleted: 2 },
                          { path: 'res://scenes/main_level.tscn', added: 4, deleted: 0 }
                        ]}
                      />
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Floating Prompt Bar at the bottom of the viewport */}
                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-full max-w-2xl px-4 z-20">
                   <PromptInterface onRunStart={handleRunStart} />
                </div>
            </div>
          </main>

          <AnimatePresence>
            {isBottomPanelOpen && (
              <motion.div 
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 280, opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ type: "spring", bounce: 0, duration: 0.4 }}
                className="shrink-0 border-t border-white/10 bg-[#080d19] overflow-hidden"
              >
                <ConsoleDock onClose={() => setIsBottomPanelOpen(false)} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Right Inspector */}
        <AnimatePresence>
          {isRightPanelOpen && (
            <motion.div 
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 320, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ type: "spring", bounce: 0, duration: 0.4 }}
              className="shrink-0 border-l border-white/5 bg-[#080d19]/80 backdrop-blur-md overflow-hidden z-20"
            >
              <NodeInspector onClose={() => setIsRightPanelOpen(false)} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Share Dialog */}
      <AnimatePresence>
        {isShareOpen && (
          <ShareDialog isOpen={isShareOpen} onClose={() => setIsShareOpen(false)} />
        )}
      </AnimatePresence>
    </div>
  );
}

function ToolButton({ icon, label, active, onClick }: { icon: React.ReactNode, label: string, active?: boolean, onClick?: () => void }) {
  return (
    <button 
      onClick={onClick}
      className={cn(
        "group relative flex h-10 w-10 items-center justify-center rounded-xl transition-all duration-200",
        active ? "bg-amber-500/10 text-amber-400 shadow-[inset_0_1px_rgba(255,255,255,0.1),0_0_15px_-3px_rgba(245,158,11,0.2)]" : "text-slate-400 hover:bg-white/5 hover:text-white"
      )}
    >
      <div className="[&>svg]:w-5 [&>svg]:h-5 [&>svg]:stroke-[1.5px]">
        {icon}
      </div>
      {/* Tooltip */}
      <div className="pointer-events-none absolute left-full ml-4 w-max rounded bg-slate-800 px-2 py-1 text-xs font-medium text-white opacity-0 shadow-xl transition-all group-hover:opacity-100 group-hover:translate-x-1">
        {label}
      </div>
    </button>
  );
}