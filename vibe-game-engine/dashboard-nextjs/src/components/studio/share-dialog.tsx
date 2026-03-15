"use client";

import { useState } from "react";
import { Download, Github, Share2, Copy, Check } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export function ShareDialog({ isOpen, onClose }: { isOpen: boolean, onClose: () => void }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 10 }}
        className="w-full max-w-md bg-[#0a0f1c] border border-white/10 rounded-2xl shadow-2xl overflow-hidden text-slate-200"
      >
        <div className="p-4 border-b border-white/5 flex items-center justify-between bg-[#0f172a]/50">
          <h2 className="text-sm font-semibold flex items-center gap-2">
            <Share2 className="w-4 h-4 text-emerald-400" />
            Share & Export Build
          </h2>
          <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-lg transition-colors text-slate-400 hover:text-white">
            ✕
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Link Share */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-widest">Share Link</label>
            <div className="flex items-center gap-2 bg-[#060913] border border-white/10 rounded-lg p-1">
              <input 
                type="text" 
                readOnly 
                value="https://vibe.engine/run/xyz_123" 
                className="flex-1 bg-transparent text-sm px-3 py-1.5 focus:outline-none text-slate-300 font-mono"
              />
              <button 
                onClick={handleCopy}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded-md transition-colors text-xs font-medium"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? 'Copied' : 'Copy'}
              </button>
            </div>
            <p className="text-[10px] text-slate-500">Anyone with this link can view and replay this generated session.</p>
          </div>

          <div className="h-px w-full bg-white/5" />

          {/* Export Options */}
          <div className="space-y-3">
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-widest">Export Artifacts</label>
            <div className="grid grid-cols-2 gap-3">
              <button className="flex flex-col items-center justify-center gap-2 p-4 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 hover:border-amber-500/30 transition-all group">
                <Download className="w-6 h-6 text-amber-500 group-hover:scale-110 transition-transform" />
                <div className="text-center">
                  <div className="text-xs font-semibold text-white">Source Project</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Godot 4.3 Folder (.zip)</div>
                </div>
              </button>
              
              <button className="flex flex-col items-center justify-center gap-2 p-4 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 hover:border-blue-500/30 transition-all group">
                <Github className="w-6 h-6 text-blue-400 group-hover:scale-110 transition-transform" />
                <div className="text-center">
                  <div className="text-xs font-semibold text-white">Push to GitHub</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Create new repo</div>
                </div>
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}