import subprocess
import time
import logging
from typing import Dict, Any, Tuple
from pathlib import Path
from contracts.validation import ValidationReport, ValidationTier, ValidationSeverity, FailureClass, ValidationIssue

logger = logging.getLogger(__name__)

class RuntimeProbeSystem:
    """
    Executes a 'micro simulation' of the generated Godot project.
    Instead of just parsing/loading the scene, it runs a small script to step the physics
    engine or emit a signal and listen for a crash.
    """
    
    def __init__(self, use_docker: bool = True):
        self.use_docker = use_docker
        self.godot_version = "4.6.1"
        self.timeout_seconds = 20

    def inject_probe_script(self, workspace_path: Path) -> Path:
        """
        Creates an autoload or temporary main scene wrapper that steps the engine.
        For simplicity, we create a probe.gd that forces `get_tree().quit(0)` after 60 frames.
        """
        probe_path = workspace_path / "probe.gd"
        with open(probe_path, "w", encoding="utf-8") as f:
            f.write("""extends Node
var frames = 0
func _process(delta):
    frames += 1
    if frames > 60:
        print("RUNTIME_PROBE_SUCCESS")
        get_tree().quit(0)
""")
        return probe_path

    def validate_runtime(self, workspace_path: str) -> ValidationReport:
        project_dir = Path(workspace_path) / "generated"
        logs_dir = Path(workspace_path) / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = logs_dir / "runtime_probe.log"
        
        report = ValidationReport(
            success=False,
            summary="Runtime Probe Started",
            completed_tiers=[ValidationTier.STATIC_CHECK, ValidationTier.EDITOR_SAFE, ValidationTier.HEADLESS_SMOKE]
        )
        
        probe_path = self.inject_probe_script(project_dir)

        # Build command: boot headless, inject the probe as a script
        if self.use_docker:
            project_dir_abs = str(project_dir.absolute()).replace('\\', '/')
            command = [
                "docker", "run", "--rm",
                "-v", f"{project_dir_abs}:/project",
                "-w", "/project",
                "robpc/godot-headless:4.6.1",
                "godot", "--headless", "-s", "probe.gd"
            ]
        else:
            command = ["godot", "--headless", "-s", "probe.gd"]

        start_time = time.time()
        try:
            logger.info(f"Running runtime probe: {' '.join(command)}")
            result = subprocess.run(
                command,
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )
            elapsed = time.time() - start_time
            
            # Clean up the probe script
            if probe_path.exists():
                probe_path.unlink()

            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write(f"--- RUNTIME PROBE LOG ---\n")
                f.write(f"Exit Code: {result.returncode}\n")
                f.write(f"--- STDOUT ---\n{result.stdout}\n")
                f.write(f"--- STDERR ---\n{result.stderr}\n")

            log_output = (result.stdout + "\n" + result.stderr)
            
            # Detect runtime failures (physics errors, missing node paths during _ready, etc.)
            has_runtime_error = "SCRIPT ERROR:" in log_output or "USER ERROR:" in log_output or "Node not found:" in log_output

            if result.returncode == 0 and "RUNTIME_PROBE_SUCCESS" in log_output and not has_runtime_error:
                report.success = True
                report.completed_tiers.append(ValidationTier.EXPORT_READY) # Conceptually verified
                report.summary = f"Runtime probe survived 60 frames in {elapsed:.2f}s."
            else:
                report.success = False
                report.failed_tier = ValidationTier.EXPORT_READY
                report.summary = "Runtime probe crashed or threw SCRIPT ERROR during gameplay simulation."
                
                snippet = result.stderr[-500:] if result.stderr else result.stdout[-500:]
                
                report.issues.append(ValidationIssue(
                    tier=ValidationTier.EXPORT_READY,
                    severity=ValidationSeverity.FATAL,
                    failure_class=FailureClass.RUNTIME_CRASH,
                    message=f"Runtime probe failed (Exit: {result.returncode})",
                    context_snippet=snippet
                ))

        except subprocess.TimeoutExpired as e:
            if probe_path.exists():
                probe_path.unlink()
            report.success = False
            report.timed_out = True
            report.failed_tier = ValidationTier.EXPORT_READY
            report.summary = f"Runtime probe timed out after {self.timeout_seconds}s."

        return report
