import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ContextExtractor:
    """
    Extracts current workspace/project info so the Planner can reason about it locally.
    In the future, this talks directly to the Godot Plugin running locally to get
    currently selected nodes or open script tabs.
    """
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        
    def get_project_summary(self) -> str:
        """Returns a summarized view of the project files and main scenes."""
        files = []
        for root, _, filenames in os.walk(self.workspace_path):
            if ".godot" in root:
                continue
            for f in filenames:
                if f.endswith(('.gd', '.tscn', '.tres', '.json')):
                    rel_path = os.path.relpath(os.path.join(root, f), self.workspace_path)
                    files.append(f"res://{rel_path}")
                    
        return f"Project Workspace Context:\nFound {len(files)} Godot assets:\n" + "\n".join(files)

    def read_script(self, rel_path: str) -> str:
        path = os.path.join(self.workspace_path, rel_path.replace("res://", ""))
        if not os.path.exists(path):
            return ""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    # Stub for future Godot editor Plugin HTTP bridge:
    def get_active_scene_tree(self) -> Dict[str, Any]:
        """Will eventually query localhost:XYZ where the Godot plugin is listening."""
        return {
            "root": "MainScene",
            "selection": ["res://player/Player.gd"]
        }
