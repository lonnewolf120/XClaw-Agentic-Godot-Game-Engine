import os
import subprocess
import time
import logging
from typing import Dict, Any, Tuple
from pathlib import Path
from contracts.validation import (
    ValidationReport, ValidationTier, ValidationSeverity, 
    FailureClass, ValidationIssue
)

logger = logging.getLogger(__name__)

class HeadlessValidator:
    """Runs tier 3 validation using a Godot headless container or local Godot binary."""
    
    def __init__(self, use_docker: bool = True):
        # Default to Docker as per Phase 0 Master Plan strategy
        self.use_docker = use_docker
        self.godot_version = "4.6.1"
        self.timeout_seconds = 15

    def validate(self, workspace_path: str) -> ValidationReport:
        project_dir = Path(workspace_path) / "generated"
        logs_dir = Path(workspace_path) / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        log_file_path = logs_dir / "headless_validation.log"
        
        report = ValidationReport(
            success=False,
            summary="Headless Validation Started",
            completed_tiers=[ValidationTier.STATIC_CHECK]
        )
        
        if not (project_dir / "project.godot").exists():
            report.success = False
            report.failed_tier = ValidationTier.STATIC_CHECK
            report.summary = "Static Check Failed: project.godot missing."
            report.issues.append(ValidationIssue(
                tier=ValidationTier.STATIC_CHECK,
                severity=ValidationSeverity.FATAL,
                failure_class=FailureClass.SCHEMA_INVALID,
                message="project.godot not found in generated dir."
            ))
            return report
            
        report.completed_tiers.append(ValidationTier.EDITOR_SAFE)

        # Build command: we just want to boot and quit cleanly, proving the script/scene compiles and loads without crash.
        # Docker fallback if Godot locally present
        if self.use_docker:
            # Containerized execution per validation architecture standard
            project_dir_abs = str(project_dir.absolute()).replace('\\', '/')
            command = [
                "docker", "run", "--rm",
                "-v", f"{project_dir_abs}:/project",
                "-w", "/project",
                "robpc/godot-headless:4.6.1",
                "godot", "--headless", "--editor", "--quit"
            ]
        else:
            command = ["godot", "--headless", "--editor", "--quit"]

        start_time = time.time()
        try:
            logger.info(f"Running headless smoke test: {' '.join(command)}")
            result = subprocess.run(
                command,
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )
            elapsed = time.time() - start_time
            
            # Write logs
            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write(f"--- HEADLESS VALIDATION LOG ---\n")
                f.write(f"Command: {' '.join(command)}\n")
                f.write(f"Exit Code: {result.returncode}\n")
                f.write(f"Elapsed Time: {elapsed:.2f}s\n")
                f.write(f"--- STDOUT ---\n{result.stdout}\n")
                f.write(f"--- STDERR ---\n{result.stderr}\n")

            report.stage_logs.append(str(log_file_path))

            if result.returncode == 0:
                report.success = True
                report.completed_tiers.append(ValidationTier.HEADLESS_SMOKE)
                report.summary = f"Headless smoke test passed in {elapsed:.2f}s."
            else:
                report.success = False
                report.failed_tier = ValidationTier.HEADLESS_SMOKE
                report.summary = f"Headless boot failed with exit code {result.returncode}."
                # Analyze logs for specific Godot errors
                failure_class = FailureClass.HEADLESS_BOOT_FAIL
                if "Parse Error:" in result.stderr or "Parse Error:" in result.stdout:
                    failure_class = FailureClass.SCRIPT_PARSE_ERROR
                
                report.issues.append(ValidationIssue(
                    tier=ValidationTier.HEADLESS_SMOKE,
                    severity=ValidationSeverity.FATAL,
                    failure_class=failure_class,
                    message=f"Godot headless process exited with {result.returncode}",
                    context_snippet=result.stderr[-500:] if result.stderr else result.stdout[-500:]
                ))

        except subprocess.TimeoutExpired as e:
            elapsed = time.time() - start_time
            report.success = False
            report.timed_out = True
            report.failed_tier = ValidationTier.HEADLESS_SMOKE
            report.summary = f"Headless smoke test timed out after {self.timeout_seconds}s."
            report.issues.append(ValidationIssue(
                tier=ValidationTier.HEADLESS_SMOKE,
                severity=ValidationSeverity.FATAL,
                failure_class=FailureClass.HEADLESS_BOOT_FAIL,
                message="Process timed out.",
            ))
            
            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write(f"--- HEADLESS VALIDATION LOG (TIMEOUT) ---\n")
                f.write(f"Command: {' '.join(command)}\n")
                f.write(f"Elapsed Time: {elapsed:.2f}s\n")
                if e.stdout: f.write(f"--- STDOUT ---\n{e.stdout.decode('utf-8', errors='ignore')}\n")
                if e.stderr: f.write(f"--- STDERR ---\n{e.stderr.decode('utf-8', errors='ignore')}\n")
            report.stage_logs.append(str(log_file_path))
            
        except Exception as e:
            report.success = False
            report.failed_tier = ValidationTier.HEADLESS_SMOKE
            report.summary = f"Headless environment execution failed: {str(e)}"
            report.issues.append(ValidationIssue(
                tier=ValidationTier.HEADLESS_SMOKE,
                severity=ValidationSeverity.FATAL,
                failure_class=FailureClass.UNKNOWN,
                message=str(e),
            ))

        return report
