import os
import shutil
from pathlib import Path
from uuid import uuid4

class WorkspaceRunner:
    def __init__(self, base_dir: str = "runs"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_workspace(self) -> str:
        """Initialize an isolated workspace for a single run following ADR."""
        run_uuid = f"run_{uuid4().hex[:8]}"
        workspace_path = self.base_dir / run_uuid
        
        # Sub-directories for strict isolation per Phase 0 logic
        (workspace_path / "input").mkdir(parents=True, exist_ok=True)
        (workspace_path / "generated").mkdir(parents=True, exist_ok=True)
        (workspace_path / "logs").mkdir(parents=True, exist_ok=True)
        (workspace_path / "validation").mkdir(parents=True, exist_ok=True)
        (workspace_path / "artifacts").mkdir(parents=True, exist_ok=True)
        (workspace_path / "replay").mkdir(parents=True, exist_ok=True)

        return str(workspace_path.absolute())

    def get_path(self, workspace_path: str, sub_dir: str) -> Path:
        """Safely fetch a deterministic subdirectory path for a workspace."""
        path = Path(workspace_path) / sub_dir
        if not path.exists():
            raise ValueError(f"Workspace path {path} does not exist. Was it created properly?")
        return path

    def write_log(self, workspace_path: str, filename: str, content: str):
        log_path = self.get_path(workspace_path, "logs") / filename
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def cleanup_workspace(self, workspace_path: str):
        path = Path(workspace_path)
        if path.exists() and "runs" in path.parts:
            shutil.rmtree(path)