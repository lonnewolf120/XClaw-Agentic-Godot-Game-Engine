import os
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ContextExtractor:
    """
    Extracts local-first project info using the Three-Tier Index:
    1. Project Index (Local files and fast AST slices)
    2. Engine API Index (Godot 4.6.1 docs RAG bounds)
    3. Workspace Memories (User preferences and selected nodes)
    
    Acts as a strict filter to prevent sending unbounded context to the LLM.
    """
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        
    def get_project_index(self) -> Dict[str, Any]:
        """
        Tier 1: Fast lexical search and dependency mapping.
        Returns a dictionary mapping extensions to list of files, and a high-level graph.
        """
        index: Dict[str, List[str]] = {".gd": [], ".tscn": [], ".tres": [], ".json": []}
        for root, _, filenames in os.walk(self.workspace_path):
            if ".godot" in root:
                continue
            for f in filenames:
                for ext in index.keys():
                    if f.endswith(ext):
                        rel_path = os.path.relpath(os.path.join(root, f), self.workspace_path)
                        index[ext].append(f"res://{rel_path}")
                        
        return {
            "file_counts": {ext: len(files) for ext, files in index.items()},
            "files": index,
            "main_scene": self._detect_main_scene()
        }
        
    def _detect_main_scene(self) -> str:
        project_file = os.path.join(self.workspace_path, "project.godot")
        if os.path.exists(project_file):
            with open(project_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if "run/main_scene=" in line:
                        return line.split("=")[1].strip().replace('"', '')
        return ""

    def get_engine_api_index(self, queries: List[str]) -> str:
        """
        Tier 2: Queries the local Godot 4.6.1 'API fact store'.
        (Currently stubbed. Will query local ChromaDB or SQLite API store)
        """
        # Placeholder for RAG API lookup. Only return relevant class fragments!
        return f"[Engine API RAG Stub] Evaluated queries: {queries}"

    def get_workspace_memories(self) -> Dict[str, Any]:
        """
        Tier 3: Retrieves user preferences and active context like selected nodes
        via Godot editor Plugin HTTP bridge (XClaw dock).
        """
        # In a live plugin mode, this queries localhost RPC:
        return {
            "root": "MainScene",
            "active_selection": ["res://player/Player.gd"],
            "coding_conventions": "Use strong typing, snake_case variables, and PascalCase classes."
        }

    def read_file_slice(self, rel_path: str, start_line: int = 0, end_line: int = -1, chunk_name: str = None) -> str:
        """
        Reads a specific snippet or named chunk (class/function) rather than whole files to save token cost.
        If chunk_name is provided, it attempts basic syntactic chunking for GDScript.
        """
        path = os.path.join(self.workspace_path, rel_path.replace("res://", ""))
        if not os.path.exists(path):
            return ""
            
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        if chunk_name and rel_path.endswith('.gd'):
            # Basic syntactic chunking for Godot/GDScript
            # Finds a func or class definition and grabs lines until the indentation resets
            in_chunk = False
            chunk_lines = []
            base_indent = 0
            
            for line in lines:
                stripped = line.strip()
                if not in_chunk:
                    if stripped.startswith(f"func {chunk_name}") or stripped.startswith(f"class {chunk_name}"):
                        in_chunk = True
                        base_indent = len(line) - len(line.lstrip())
                        chunk_lines.append(line)
                else:
                    current_indent = len(line) - len(line.lstrip())
                    if line.strip() == "" or current_indent > base_indent:
                        chunk_lines.append(line)
                    else:
                        break # Indentation returned to base level, function ended
            
            if chunk_lines:
                return "".join(chunk_lines)
                
        # Fallback to line slicing
        if end_line == -1:
            end_line = len(lines)
            
        return "".join(lines[start_line:end_line])

    def get_file_hash(self, rel_path: str) -> str:
        """Returns SHA-256 hash of a file for caching invalidation."""
        import hashlib
        path = os.path.join(self.workspace_path, rel_path.replace("res://", ""))
        if not os.path.exists(path):
            return ""
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    def get_context_bundle(self) -> Dict[str, Any]:
        """Returns the fully bounded, cost-optimized context payload."""
        return {
            "project": self.get_project_index(),
            "memories": self.get_workspace_memories()
        }
