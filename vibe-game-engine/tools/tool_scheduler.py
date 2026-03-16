import logging
from typing import List, Dict, Any, Tuple
from contracts.actions import ActionBatch, GodotActionWrapper

logger = logging.getLogger(__name__)

class ToolScheduler:
    """
    Breaks a single large Builder ActionBatch into staged execution layers to prevent cascading failures.
    For example, it ensures a script is created and valid before attempting to attach it to a node.
    """
    def __init__(self):
        pass

    def schedule(self, batch: ActionBatch) -> List[List[GodotActionWrapper]]:
        """
        Takes an unordered or linear ActionBatch and groups actions into dependent stages.
        Returns a list of stages (each stage is a list of wrappers).
        
        Stage 1: Safe File Creation (create_script)
        Stage 2: Scene Node Creation (create_node)
        Stage 3: Node Properties (set_property)
        Stage 4: Structural Attachments (attach_script, connect_signal)
        Stage 5: Patches (patch_script)
        Stage 6: Save (save_scene)
        """
        stages = {
            "file_creation": [],
            "node_creation": [],
            "node_properties": [],
            "attachments": [],
            "patches": [],
            "saves": []
        }
        
        for wrapper in batch.actions:
            if wrapper.action_type == "create_script":
                stages["file_creation"].append(wrapper)
            elif wrapper.action_type == "create_node":
                stages["node_creation"].append(wrapper)
            elif wrapper.action_type == "set_property":
                stages["node_properties"].append(wrapper)
            elif wrapper.action_type in ["attach_script", "connect_signal"]:
                stages["attachments"].append(wrapper)
            elif wrapper.action_type == "patch_script":
                stages["patches"].append(wrapper)
            elif wrapper.action_type == "save_scene":
                stages["saves"].append(wrapper)
            else:
                # Default fallback
                stages["patches"].append(wrapper)

        # Build final scheduled order, excluding empty stages
        scheduled_pipeline = []
        for stage_key in ["file_creation", "node_creation", "node_properties", "attachments", "patches", "saves"]:
            if stages[stage_key]:
                scheduled_pipeline.append(stages[stage_key])
                
        logger.info(f"ToolScheduler broke batch into {len(scheduled_pipeline)} execution stages.")
        return scheduled_pipeline
