from __future__ import annotations
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import Field, StrictBool, StrictStr, conint
from contracts.base import StrictModel

class ActionType(str, Enum):
    CREATE_NODE = "create_node"
    SET_PROPERTY = "set_property"
    ATTACH_SCRIPT = "attach_script"
    CREATE_SCRIPT = "create_script"
    CONNECT_SIGNAL = "connect_signal"
    SAVE_SCENE = "save_scene"
    RUN_VALIDATION = "run_validation"

class EngineAction(StrictModel):
    action_type: ActionType
    parameters: Dict[str, Any] = Field(default_factory=dict)

class ActionBatch(StrictModel):
    actions: List[EngineAction] = Field(default_factory=list)
