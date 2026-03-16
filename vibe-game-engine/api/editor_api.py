import logging
import json
from typing import Dict, Any

from fastapi import APIRouter, HTTPException

from contracts.api_schemas import (
    PatchProposalRequest, 
    PatchProposalResponse, 
    ApplyPatchRequest, 
    ApplyPatchResponse,
    ValidationResult
)
from contracts.actions import ActionBatch, PatchScriptAction
from store.run_store import RunStore
from agents.builder import ActionBuilderAgent
from tools.context_extractor import ContextExtractor
from tools.local_executor import LocalGodotExecutor
from validation.headless_runner import HeadlessValidator
from contracts.messages import PlanMessage

router = APIRouter(prefix="/v1/editor", tags=["Editor Plugin API"])
logger = logging.getLogger(__name__)

store = RunStore()

def _generate_diff_preview(batch: ActionBatch) -> str:
    """Creates a basic human readable diff representation of the patch intent."""
    preview = []
    for wrapper in batch.actions:
        action = getattr(wrapper, wrapper.action_type, None)
        if isinstance(action, PatchScriptAction):
            preview.append(f"--- {action.script_path}")
            preview.append(f"+++ {action.script_path}")
            preview.append(f"@@ (patch) @@")
            preview.append(f"- {action.search_string}" if action.search_string else "")
            preview.append(f"+ {action.replace_string}")
        else:
            preview.append(f">> Executing {wrapper.action_type}")
    return "\n".join(preview)


@router.post("/propose_patch", response_model=PatchProposalResponse)
def propose_patch(request: PatchProposalRequest):
    """
    Called by the Godot plugin. Extracts local context, formats it, 
    sends via LangChain to Vertex API, and returns an ActionBatch for user review.
    Does NOT execute writes locally.
    """
    # 1. Extract Local Context (Privacy boundary: we control this completely)
    extractor = ContextExtractor(request.workspace_path)
    context_summary = extractor.get_project_summary()
    
    # Optional privacy mode logic
    if request.mode == "minimal_context":
        # we would only read files explicitly selected in request.selection
        pass
        
    # 2. Call the Remote Vertex Brain
    builder = ActionBuilderAgent()
    # Note: Using mock plan as a pass-through for Stage 1. Later the Planner agent sits here.
    dummy_plan = PlanMessage(
        archetype="patch", 
        goals=[request.prompt],
        mechanics=[], constraints=[], asset_requirements=[], risk_flags=["direct file modification"]
    )
    
    try:
        action_batch = builder.generate_action_batch(request.prompt, dummy_plan, context_summary)
    except Exception as e:
        logger.error(f"Vertex Builder failed: {e}")
        raise HTTPException(status_code=502, detail="Failed to get valid patch from AI")
        
    # 3. Store Proposal
    proposal_id = store.store_proposal(request.workspace_path, action_batch)

    # 4. Generate Diff
    diff = _generate_diff_preview(action_batch)
    
    # 5. Calculate Affected Files Security Bounds
    affected = []
    for wrapper in action_batch.actions:
        a = getattr(wrapper, wrapper.action_type, None)
        if a:
            if hasattr(a, 'script_path'): affected.append(a.script_path)
            elif hasattr(a, 'node_path'): affected.append(a.node_path)
    
    return PatchProposalResponse(
        proposal_id=proposal_id,
        action_batch=action_batch,
        diff_preview=diff,
        risk_flags=["unverified syntax"],
        affected_files=list(set(affected))
    )

@router.post("/apply_patch", response_model=ApplyPatchResponse)
def apply_patch(request: ApplyPatchRequest):
    """
    Called by the Godot plugin after user approves the diff preview.
    Executes the validated ActionBatch safely, runs Headless Validation, and commits run.
    """
    # 1. Load Trusted Batch
    prop = store.load_proposal(request.proposal_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Proposal not found")
        
    batch = ActionBatch.model_validate_json(prop.action_batch_json)
    
    # 2. Local Safe Execution
    import os
    abs_workspace = os.path.abspath(prop.workspace_path)
    executor = LocalGodotExecutor(abs_workspace)
    
    success = executor.execute_batch(batch)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to apply patch locally. Check backend logs.")
        
    # 3. Execute Headless Smoke Validation
    validator = HeadlessValidator(use_docker=False)
    report = validator.validate(abs_workspace)
    
    # 4. Persist (Creating a proper RunState conceptually for logging)
    run_state = store.create_run(f"Applied Proposal {request.proposal_id}", prop.workspace_path)
    run_state.validation_report = report
    store.update_run(run_state)
    
    return ApplyPatchResponse(
        run_id=run_state.run_id,
        status="COMPLETED" if report.success else "FAILED",
        validation_result=ValidationResult(success=report.success, summary=report.summary),
        artifacts=[],
        rollback_available=False # To be implemented
    )
