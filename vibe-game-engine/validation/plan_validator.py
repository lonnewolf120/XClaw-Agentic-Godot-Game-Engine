import logging
import os
from typing import List, Dict, Any, Tuple
from contracts.actions import ActionBatch

logger = logging.getLogger(__name__)

class PlanValidator:
    """
    Non-LLM heuristic check applied immediately after the Builder generates an ActionBatch.
    Verifies targets exist in the project and types match before burning execution/validation loops.
    """
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path

    def validate_batch(self, batch: ActionBatch) -> Tuple[bool, List[str]]:
        """
        Returns (is_valid, list_of_errors).
        If errors exist, this fails back to the Builder locally without executing.
        """
        errors = []
        for idx, wrapper in enumerate(batch.actions):
            action_type = wrapper.action_type
            action = getattr(wrapper, action_type, None)
            
            if not action:
                errors.append(f"Action {idx} missing payload for {action_type}.")
                continue
                
            if action_type == "attach_script" or action_type == "patch_script":
                # Ensure the script exists in workspace if we are patching or attaching
                # Note: create_script might have run earlier in the pipeline, 
                # but static validation ensures the referenced path is at least syntactically correct.
                if not action.script_path.startswith("res://"):
                    errors.append(f"Action {idx} ({action_type}): script_path must start with res://")
                    
                if action_type == "patch_script":
                    rel_path = action.script_path.replace("res://", "").lstrip('/')
                    full_path = os.path.join(self.workspace_path, rel_path)
                    if not os.path.exists(full_path):
                         # If we are patching, the file MUST exist on disk right now
                         errors.append(f"Action {idx} (patch_script): Cannot patch non-existent file {rel_path}")

            elif action_type == "connect_signal":
                 if not action.signal_name:
                     errors.append(f"Action {idx} (connect_signal): missing signal_name.")
                     
        is_valid = len(errors) == 0
        if not is_valid:
            logger.warning(f"PlanValidator caught {len(errors)} heuristic errors.")
            
        return is_valid, errors
