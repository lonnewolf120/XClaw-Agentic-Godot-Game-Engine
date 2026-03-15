import { useEffect, useState } from "react";
import { Server, Monitor, Gamepad2, AlertCircle } from "lucide-react";
import { cn } from "../../lib/utils";

export function ServiceStatus() {
  const [backendStatus, setBackendStatus] = useState<"checking" | "up" | "down">("checking");
  const [godotStatus, setGodotStatus] = useState<"checking" | "up" | "down">("checking");
  const [frontendStatus] = useState<"up">("up"); // Always up if React is rendering
  const [backendErrors, setBackendErrors] = useState<string[]>([]);
  
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/v1/health", { cache: "no-store", mode: "cors" });
        if (res.ok) {
          const data = await res.json();
          setBackendStatus("up");
          if (data.errors && data.errors.length > 0) {
             setBackendErrors(data.errors);
          } else {
             setBackendErrors([]);
          }
        } else {
          setBackendStatus("down");
        }
      } catch (err) {
        setBackendStatus("down");
        setBackendErrors(["Connection to 127.0.0.1:8000 refused. Is the FastAPI server running?"]);
      }
      
      // Check Godot mock status (can be expanded later if Godot bridge exposes an API)
      setGodotStatus("up");
    };

    checkStatus();
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center gap-4 bg-black/40 px-3 py-1.5 rounded-lg border border-white/5">
      {/* Frontend */}
      <div className="flex items-center gap-1.5" title="Next.js Dashboard">
         <Monitor className={cn("h-3.5 w-3.5", frontendStatus === "up" ? "text-emerald-500" : "text-red-500")} />
         <span className="text-[10px] font-mono uppercase text-slate-400">UI</span>
         <div className={cn("h-1.5 w-1.5 rounded-full", frontendStatus === "up" ? "bg-emerald-500" : "bg-red-500")} />
      </div>
      
      <div className="w-px h-3 bg-white/10" />

      {/* Backend */}
      <div className="flex items-center gap-1.5 group relative" title="Python FastAPI Backend">
         <Server className={cn("h-3.5 w-3.5", backendStatus === "up" ? "text-emerald-500" : backendStatus === "checking" ? "text-amber-500" : "text-red-500")} />
         <span className="text-[10px] font-mono uppercase text-slate-400">API</span>
         <div className={cn("h-1.5 w-1.5 rounded-full", backendStatus === "up" ? "bg-emerald-500" : backendStatus === "checking" ? "bg-amber-500 animate-pulse" : "bg-red-500")} />
         
         {backendErrors.length > 0 && (
           <div className="hidden group-hover:flex absolute top-full mt-2 right-0 flex-col gap-1 z-50 bg-red-950/90 border border-red-500/50 p-2 rounded text-xs text-red-200 min-w-xs shadow-xl backdrop-blur-md whitespace-nowrap">
              <div className="flex items-center gap-1 border-b border-red-500/30 pb-1 mb-1 font-bold">
                 <AlertCircle className="h-3 w-3" /> Backend Errors
              </div>
              {backendErrors.map((err, i) => (
                 <div key={i}>• {err}</div>
              ))}
           </div>
         )}
      </div>

      <div className="w-px h-3 bg-white/10" />

      {/* Godot */}
      <div className="flex items-center gap-1.5" title="Godot Headless Engine">
         <Gamepad2 className={cn("h-3.5 w-3.5", godotStatus === "up" ? "text-emerald-500" : "text-red-500")} />
         <span className="text-[10px] font-mono uppercase text-slate-400">Godot</span>
         <div className={cn("h-1.5 w-1.5 rounded-full", godotStatus === "up" ? "bg-emerald-500" : "bg-red-500")} />
      </div>
    </div>
  );
}