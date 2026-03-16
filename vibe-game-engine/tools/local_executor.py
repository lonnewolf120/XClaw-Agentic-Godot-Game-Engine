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
        
    def preview_batch(self, batch: ActionBatch) -> Dict[str, Any]:
        """
        Returns a dry-run preview of the batch changes for Human-in-the-Loop review.
        """
        preview = {
            "description": batch.description,
            "actions": [],
            "files_changed": set()
        }
        
        for wrapper in batch.actions:
            action_type = wrapper.action_type
            action_model = getattr(wrapper, action_type, None)
            
            if action_type == "create_script":
                preview["actions"].append(f"Create/Overwrite script {action_model.script_path}")
                preview["files_changed"].add(action_model.script_path)
            elif action_type == "patch_script":
                preview["actions"].append(f"Patch script {action_model.script_path}: replacing '{action_model.search_string[:20]}...'")
                preview["files_changed"].add(action_model.script_path)
            elif action_type == "create_node":
                preview["actions"].append(f"Create node {action_model.node_name} ({action_model.node_type}) at {action_model.parent_path}")
                
        preview["files_changed"] = list(preview["files_changed"])
        return preview

    def execute_batch(self, batch: ActionBatch) -> bool:
        """
        Executes the sequence of schema actions.
        In the future Godot fork, this will map to EditorUndoRedoManager transactions.
        For now, we execute linear file changes.
        """
        logger.info(f"Executing batch: {batch.description}")
        
        # Conceptually start transaction here
        # godot_undo_redo.create_action("AI Edit: " + batch.description)
        
        for idx, wrapper in enumerate(batch.actions):
            action_type = wrapper.action_type
            action_model = getattr(wrapper, action_type, None)
            if not action_model:
                logger.error(f"Action {idx} has missing payload for {action_type}")
                return False

            try:
                if action_type == "patch_script":
                    self._patch_script(action_model)
                elif action_type == "create_script":
                    self._create_script(action_model)
                elif action_type == "create_node":
                    self._create_node(action_model)
                # ... implement other actions mapping directly to .tscn text parsing or plugin RPC ...
                else:
                    logger.warning(f"Unimplemented action: {action_type}")
            except Exception as e:
                logger.error(f"Failed executing action {idx} ({action_type}): {e}")
                # Conceptually rollback here if we had a live editor connection
                # godot_undo_redo.undo()
                return False

        # Conceptually commit transaction here
        # godot_undo_redo.commit_action()
        return True
    def _create_script(self, action):
        import os
        script_path = action.script_path.replace("res://", "").lstrip('/')
        file_path = os.path.join(self.workspace_path, script_path)
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write exact content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(action.content)

    def _patch_script(self, action): # Pydantic model
        import os
        script_path = action.script_path.replace("res://", "").lstrip('/')
        file_path = os.path.join(self.workspace_path, script_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if action.search_string not in content:
            raise ValueError(f"String not found in {script_path}:\n{action.search_string}")

        new_content = content.replace(action.search_string, action.replace_string)
