from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import Field, StrictStr
from contracts.base import StrictModel
from contracts.action_schema import ActionBatch
from contracts.validation import ValidationReport
from contracts.godot_patch import PatchBatch

class PlanTask(StrictModel):
    id: StrictStr
    role: StrictStr
    goal: StrictStr

class PlanMessage(StrictModel):
    type: StrictStr = "plan"
    archetype: StrictStr = "platformer"
    goals: List[StrictStr] = Field(default_factory=list)
    mechanics: List[StrictStr] = Field(default_factory=list)
    constraints: List[StrictStr] = Field(default_factory=list)
    asset_requirements: List[StrictStr] = Field(default_factory=list)
    risk_flags: List[StrictStr] = Field(default_factory=list)
    tasks: List[PlanTask] = Field(default_factory=list)

class ActionSchemaMessage(StrictModel):
    type: StrictStr = "action_batch"
    actions: ActionBatch

class ValidationResultMessage(StrictModel):
    type: StrictStr = "validation_result"
    report: ValidationReport

class DebugPatchMessage(StrictModel):
    type: StrictStr = "debug_patch"
    patch: PatchBatch

class RunCompleteMessage(StrictModel):
    type: StrictStr = "run_complete"
    artifacts: List[StrictStr] = Field(default_factory=list)
    smoke_test_pass: bool = False
