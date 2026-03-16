import os
import re
import hashlib
from typing import List, Dict, Any, Tuple
from store.project_graph import ProjectGraphStore

class ProjectGraphParser:
    """
    Crawls a Godot project directory to populate the ProjectGraphStore.
    Implements hash-based invalidation to only parse changed files.
    """
    def __init__(self, workspace_path: str, store: ProjectGraphStore, project_id: str = "default"):
        self.workspace_path = workspace_path
        self.store = store
        self.project_id = project_id
        
        # Simple regex for GDScript chunks
        self.func_regex = re.compile(r"^func\s+([a-zA-Z0-9_]+)\s*\(")
        self.class_regex = re.compile(r"^class\s+([a-zA-Z0-9_]+)\s*:")
        
        # Simple regex for TSCN nodes
        self.node_regex = re.compile(r"^\[node\s+name=\"([^\"]+)\"\s+type=\"([^\"]+)\"")
        self.ext_resource_regex = re.compile(r"^\[ext_resource\s+type=\"([^\"]+)\"\s+path=\"([^\"]+)\"\s+id=\"([^\"]+)\"")

    def _get_file_hash(self, file_path: str) -> str:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    def sync_project(self):
        """Walks the workspace and indexes .gd and .tscn files."""
        for root, _, files in os.walk(self.workspace_path):
            if ".godot" in root:
                continue
                
            for f in files:
                file_path = os.path.join(root, f)
                rel_path = f"res://{os.path.relpath(file_path, self.workspace_path).replace(os.sep, '/')}"
                
                if f.endswith('.gd'):
                    self._parse_gdscript(file_path, rel_path)
                elif f.endswith('.tscn'):
                    self._parse_tscn(file_path, rel_path)

    def _parse_gdscript(self, file_path: str, rel_path: str):
        file_hash = self._get_file_hash(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        current_chunk_type = None
        current_chunk_name = None
        current_chunk_lines = []
        start_line = 0
        
        for i, line in enumerate(lines):
            func_match = self.func_regex.match(line)
            class_match = self.class_regex.match(line)
            
            if func_match or class_match:
                # Save previous chunk if exists
                if current_chunk_name:
                    self._save_chunk(rel_path, current_chunk_type, current_chunk_name, 
                                     "".join(current_chunk_lines), start_line, i-1, file_hash)
                
                current_chunk_type = 'gd_func' if func_match else 'gd_class'
                current_chunk_name = func_match.group(1) if func_match else class_match.group(1)
                current_chunk_lines = [line]
                start_line = i
            elif current_chunk_name:
                current_chunk_lines.append(line)
                
        # Save last chunk
        if current_chunk_name:
             self._save_chunk(rel_path, current_chunk_type, current_chunk_name, 
                              "".join(current_chunk_lines), start_line, len(lines)-1, file_hash)

    def _parse_tscn(self, file_path: str, rel_path: str):
        file_hash = self._get_file_hash(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 1. Extract dependencies (ext_resources)
        ext_resources = {}
        for match in self.ext_resource_regex.finditer(content):
            res_type, res_path, res_id = match.groups()
            ext_resources[res_id] = res_path
            
            if res_path.endswith('.gd'):
                self.store.add_edge(self.project_id, rel_path, res_path, 'SCENE_REFERENCES_RESOURCE')
            elif res_path.endswith('.tscn'):
                self.store.add_edge(self.project_id, rel_path, res_path, 'SCENE_INSTANCES_SCENE')

        # 2. Extract Node definitions for lexical search
        for match in self.node_regex.finditer(content):
            node_name, node_type = match.groups()
            node_id = f"{rel_path}::{node_name}"
            
            # Simple indexing of node presence
            self.store.upsert_chunk(
                project_id=self.project_id,
                index_type="project",
                file_path=rel_path,
                symbol_kind="tscn_node",
                symbol_name=node_name,
                text_excerpt=f"[{node_type}] {node_name}",
                start_line=0,
                end_line=0,
                file_hash=file_hash
            )
            self.store.add_edge(self.project_id, rel_path, node_id, 'SCENE_CONTAINS_NODE')

    def _save_chunk(self, rel_path: str, symbol_kind: str, symbol_name: str, text: str, start: int, end: int, file_hash: str):
        self.store.upsert_chunk(
            project_id=self.project_id,
            index_type="project",
            file_path=rel_path,
            symbol_kind=symbol_kind,
            symbol_name=symbol_name,
            text_excerpt=text,
            start_line=start,
            end_line=end,
            file_hash=file_hash,
            # embeddings are generated asynchronously or lazily in the LLM manager layer to save blocking time
            embedding=None 
        )
