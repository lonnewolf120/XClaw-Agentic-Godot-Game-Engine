# Phase 3 Session Benchmark Matrix
import os
import argparse
import logging
from typing import List, Dict, Any

import subprocess
from pathlib import Path

def run_multi_project_benchmark():
    projects = [
        "tests/clean_project",
        "tests/medium_project", 
        "tests/messy_project"
    ]
    
    print("Beginning Multi-Project Execution Matrix...")
    
    base_dir = Path(os.getcwd())
    script_path = base_dir / "vibe-game-engine" / "scripts" / "long_session_benchmark.py"
    
    for proj in projects:
        print(f"\nEvaluating: {proj}")
        target_ws = base_dir / proj
        log_file = base_dir / f"{os.path.basename(proj)}_benchmark.log"
        
        # We invoke the long session benchmark script via subprocess to fully isolate its environment
        cmd = ["python", str(script_path), "--workspace", str(target_ws)]
        
        print(f"Running: {' '.join(cmd)}")
        try:
            with open(log_file, "w") as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, text=True)
            print(f"[PASS] Evaluated {proj}. Logs written to {log_file}")
        except Exception as e:
            print(f"[FAIL] Exception during evaluation of {proj}: {e}")

if __name__ == "__main__":
    run_multi_project_benchmark()
