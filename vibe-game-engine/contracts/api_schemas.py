import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from contracts.base import StrictModel
from contracts.actions import ActionBatch

class PatchProposalRequest(BaseModel):
    prompt: str = Field(..., description="The user intent, e.g., 'Make player jump higher'")
    workspace_path: str = Field(..., description="Absolute path to the local Godot project directory")
    selection: Optional[List[str]] = Field(default=None, description="Paths of currently selected files/nodes")
    mode: str = Field(default="project_aware", description="Either 'minimal_context' or 'project_aware'")

class PatchProposalResponse(StrictModel):
    proposal_id: str
    action_batch: ActionBatch
    diff_preview: str = Field(..., description="Human readable diff representation")
    risk_flags: List[str] = Field(default_factory=list)
    affected_files: List[str] = Field(default_factory=list)

class ApplyPatchRequest(BaseModel):
    proposal_id: str

class ValidationResult(StrictModel):
    success: bool
    summary: str

class ApplyPatchResponse(StrictModel):
    run_id: str
    status: str
    validation_result: ValidationResult
    artifacts: List[str]
    rollback_available: bool

class RollbackRequest(BaseModel):
    run_id: str
