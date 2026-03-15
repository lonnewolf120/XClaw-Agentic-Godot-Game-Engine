from typing import List, Dict, Any, Optional, Literal
from pydantic import Field
from contracts.base import StrictModel

class BaseGodotAction(StrictModel):
    action_type: str = Field(..., description="The type of action to perform")

class CreateNodeAction(BaseGodotAction):
    action_type: Literal["create_node"] = "create_node"
    node_type: str = Field(..., description="e.g., 'CharacterBody2D', 'Sprite2D'")
    node_name: str = Field(..., description="Name of the new node")
    parent_path: str = Field(default=".", description="Node path relative to scene root, '.' for root")

class SetPropertyAction(BaseGodotAction):
    action_type: Literal["set_property"] = "set_property"
    node_path: str = Field(..., description="Path to the target node")
    property_name: str = Field(..., description="The name of the property, e.g., 'position', 'texture'")
    value: Any = Field(..., description="The value to set (can be number, string, dict for Vector2, etc.)")
    value_type: str = Field(default="auto", description="Optional type hint: 'Vector2', 'Color', 'Resource', 'int'")

class AttachScriptAction(BaseGodotAction):
    action_type: Literal["attach_script"] = "attach_script"
    node_path: str = Field(..., description="Path to target node")
    script_path: str = Field(..., description="res:// path to the local GDScript file")

class ConnectSignalAction(BaseGodotAction):
    action_type: Literal["connect_signal"] = "connect_signal"
    source_node: str = Field(..., description="Path to emitting node")
    signal_name: str = Field(..., description="e.g., 'body_entered'")
    target_node: str = Field(..., description="Path to receiving node")
    method_name: str = Field(..., description="Method to call on target node")

class PatchScriptAction(BaseGodotAction):
    action_type: Literal["patch_script"] = "patch_script"
    script_path: str = Field(..., description="res:// path to the GDScript")
    search_string: str = Field(..., description="Exact string to replace")
    replace_string: str = Field(..., description="New string to insert")

class SaveSceneAction(BaseGodotAction):
    action_type: Literal["save_scene"] = "save_scene"
    scene_path: str = Field(..., description="res:// path to save the current scene state")

class ActionBatch(StrictModel):
    """A collection of actions to be executed sequentially by the Local Executor"""
    description: str = Field(..., description="What this batch is trying to achieve")
    actions: List[Any] = Field(..., description="List of BaseGodotAction subclasses")
    
