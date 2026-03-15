import json
import logging
from typing import Dict, Any

from contracts.actions import ActionBatch

logger = logging.getLogger(__name__)

class LocalGodotExecutor:
    """
    Consumes a generalized ActionBatch from the AI and maps it into safe, 
    local deterministic file writes and Godot structural changes.
    """
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        
    def execute_batch(self, batch: ActionBatch) -> bool:
        """Executes the sequence of schema actions."""
        logger.info(f"Executing batch: {batch.description}")
        
        for idx, action in enumerate(batch.actions):
            action_type = action.get("action_type")
            try:
                if action_type == "patch_script":
                    self._patch_script(action)
                elif action_type == "create_node":
                    self._create_node(action)
                # ... implement other actions mapping directly to .tscn text parsing or plugin RPC ...
                else:
                    logger.warning(f"Unimplemented action: {action_type}")
            except Exception as e:
                logger.error(f"Failed executing action {idx} ({action_type}): {e}")
                return False
                
        return True
        
    def _patch_script(self, action: Dict[str, Any]):
        script_path = action["script_path"].replace("res://", "")
        file_path = f"{self.workspace_path}/{script_path}"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if action["search_string"] not in content:
            raise ValueError(f"String not found in {script_path}:\n{action['search_string']}")
            
        new_content = content.replace(action["search_string"], action["replace_string"])
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
