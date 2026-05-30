import os
import json
import uuid
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from store.run_store import RunStore
from agents.intent_classifier import IntentClassifier
from store.project_graph import ProjectGraphStore
from agents.retrieval_orchestrator import RetrievalOrchestrator
from agents.planner import PlannerAgent
from agents.builder import ActionBuilderAgent
from contracts.messages import PlanMessage, PlanTask
from contracts.actions import ActionBatch
from contracts.run_state import RunState, RunStatus, OrchestrationNode
from api.activity_monitor import activity_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plugin", tags=["Godot Plugin Bridge"])

class NodeContext(BaseModel):
    name: str
    class_name: str = Field(alias="class", default="")
    path: str

class ProposalRequest(BaseModel):
    prompt: str
    options: dict = Field(default_factory=dict)
    selection: List[NodeContext] = []
    current_scene_path: Optional[str] = None
    project_path: Optional[str] = None
    mode: Optional[str] = "scene_mutation"
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None

class ApplyRequest(BaseModel):
    proposal_id: str
    native_receipts: List[Dict[str, Any]] = []
    apply_status: str = "success"
    editor_validation_status: str = "passed"
    approved_actions: List[Dict[str, Any]] = []

# Persistent stores
run_store = RunStore()
pending_proposals_queue = []


def get_plugin_queue_length() -> int:
    return len(pending_proposals_queue)


def _fallback_proposal_response(prompt: str, provider: str, model_name: str, message: str) -> Dict[str, Any]:
    logger.error("Returning fallback proposal response: %s", message)
    return {
        "proposal_id": f"prop_fallback_{uuid.uuid4().hex[:8]}",
        "llm_provider": provider,
        "llm_model": model_name,
        "intent": {
            "is_asset_request": False,
            "is_script_patch": False,
            "is_scene_mutation": True,
            "is_new_feature": False,
            "primary_focus": "scene",
        },
        "actions": [],
        "diff_preview": [f"Backend fallback: {message}", f"Prompt: {prompt[:120]}"],
        "risk_flags": ["backend_fallback"],
        "retrieval_summary": {"lexical": 0, "graph": 0},
        "token_summary": {"status": "fallback"},
    }

@router.post("/enqueue_proposal")
async def enqueue_proposal(req: Dict[str, Any]):
    """Called by dashboard to push a generated proposal to Godot."""
    pending_proposals_queue.append(req)
    activity_monitor.record(
        level="info",
        source="plugin_bridge",
        event_type="enqueue_proposal",
        message="Dashboard enqueued proposal for plugin",
        details={"queue_length": len(pending_proposals_queue), "proposal_id": req.get("proposal_id", "")},
    )
    return {"status": "enqueued", "queue_length": len(pending_proposals_queue)}

@router.get("/poll")
async def poll_proposals():
    """Called by Godot every 2 seconds to check if dashboard pushed anything."""
    if pending_proposals_queue:
        event = pending_proposals_queue.pop(0)
        activity_monitor.record(
            level="info",
            source="plugin_bridge",
            event_type="poll_proposals",
            message="Plugin polled and received proposal",
            details={"queue_length": len(pending_proposals_queue), "proposal_id": event.get("proposal_id", "")},
        )
        return event
    return {"status": "empty"}


@router.get("/status")
async def plugin_bridge_status():
    return {
        "status": "ok",
        "queue_length": len(pending_proposals_queue),
        "bridge": "plugin",
    }

@router.post("/proposal")
async def create_proposal(req: ProposalRequest):
    provider = req.llm_provider or req.options.get("llm_provider") or os.environ.get("XCLAW_LLM_PROVIDER") or "gemini"
    model_name = req.llm_model or req.options.get("llm_model") or os.environ.get("XCLAW_LLM_MODEL") or "gemini-3.1-pro-preview"

    try:
        activity_monitor.record(
            level="info",
            source="plugin_bridge",
            event_type="create_proposal_start",
            message="Creating proposal",
            details={"provider": provider, "model": model_name, "mode": req.mode},
        )
        if req.options.get("api_key"):
            os.environ["GEMINI_API_KEY"] = str(req.options["api_key"])
        if req.options.get("gemini_cli_cmd"):
            os.environ["XCLAW_GEMINI_CLI_CMD"] = str(req.options["gemini_cli_cmd"])
        if req.options.get("copilot_cli_cmd"):
            os.environ["XCLAW_COPILOT_CLI_CMD"] = str(req.options["copilot_cli_cmd"])
        if req.options.get("codex_cli_cmd"):
            os.environ["XCLAW_CODEX_CLI_CMD"] = str(req.options["codex_cli_cmd"])

        use_mock = str(req.options.get("use_mock", "false")).lower() == "true"
            
        project_path = req.project_path
        if not project_path:
            project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dummy_proj"))

        db_path = os.path.join(project_path, "project_graph.db")

        # 1. Create Run in Store
        run_state = run_store.create_run(req.prompt, project_path)

        # 2. Intent Classifier
        classifier = IntentClassifier()
        intent = classifier.classify(req.prompt)

        # 3. Retrieval Orchestrator
        retrieved: Dict[str, Any] = {}
        context_summary = ""
        try:
            store = ProjectGraphStore(db_path)
            orchestrator = RetrievalOrchestrator(store)
            paths = [n.path for n in req.selection]
            retrieved = orchestrator.retrieve_for_prompt(req.prompt, paths)
            context_summary = retrieved.get("formatted_context", "")
        except Exception as retrieval_error:
            logger.exception("Retrieval pipeline degraded: %s", retrieval_error)
            retrieved = {"lexical_results": [], "graph_results": []}
            context_summary = ""

        # 4. Planner
        plan: PlanMessage
        try:
            planner = PlannerAgent(model_name=model_name, provider=provider, use_mock=use_mock)
            plan = planner.plan(f"Context:\n{context_summary}\n\nUser Request: {req.prompt}")
        except Exception as planner_error:
            logger.exception("Planner degraded: %s", planner_error)
            plan = PlanMessage(
                archetype="platformer",
                goals=["Fallback plan due to planner error"],
                mechanics=[],
                constraints=[],
                asset_requirements=[],
                risk_flags=[f"planner_error:{planner_error}"],
                tasks=[PlanTask(id="1", role="builder", goal="Generate safe no-op action batch")],
            )
        run_state.plan = plan
        run_store.update_run(run_state)

        # 5. Builder
        builder = ActionBuilderAgent(provider=provider, model_name=model_name)
        selection_context = f"Selected Nodes: {json.dumps([s.model_dump() for s in req.selection])}\nCurrent Scene: {req.current_scene_path}"
        full_context = f"{selection_context}\n\n{context_summary}"

        plan_summary = json.dumps(plan.model_dump(), ensure_ascii=True)
        try:
            action_batch = builder.generate_action_batch(req.prompt, plan_summary, full_context)
        except Exception as builder_error:
            logger.exception("Builder degraded: %s", builder_error)
            action_batch = ActionBatch(actions=[], description=f"Builder error: {builder_error}")

        # 6. Transform to Wave 1 Action List (Native mapping)
        actions = []
        if action_batch and getattr(action_batch, "actions", None):
            for wrapper in action_batch.actions:
                action_type = wrapper.action_type
                # Extract the underlying typed payload
                payload_obj = getattr(wrapper, action_type, None)
                if payload_obj:
                    payload_dict = payload_obj.model_dump()
                    # Remove redundant 'action_type' from params
                    if "action_type" in payload_dict:
                        del payload_dict["action_type"]
                    actions.append({
                        "type": action_type,
                        "params": payload_dict
                    })

        # Save proposal for reference
        try:
            proposal_id = run_store.store_proposal(project_path, action_batch)
        except Exception as store_error:
            logger.exception("Proposal store degraded: %s", store_error)
            proposal_id = f"prop_mem_{uuid.uuid4().hex[:8]}"

        # Return response payload
        return {
            "proposal_id": proposal_id,
            "llm_provider": provider,
            "llm_model": model_name,
            "intent": intent,
            "actions": actions,
            "diff_preview": [getattr(action_batch, "description", "")] if action_batch else [],
            "risk_flags": ["real_ai_generated"],
            "retrieval_summary": {
                "lexical": len(retrieved.get("lexical_results", [])),
                "graph": len(retrieved.get("graph_results", []))
            },
            "token_summary": {"status": "untracked_for_now"}
        }
    except Exception as e:
        activity_monitor.record(
            level="error",
            source="plugin_bridge",
            event_type="create_proposal_error",
            message="Unhandled proposal failure",
            details={"error": str(e), "provider": provider, "model": model_name},
        )
        logger.exception("Unhandled proposal failure: %s", e)
        return _fallback_proposal_response(req.prompt, provider, model_name, str(e))


@router.post("/apply")
async def apply_proposal(req: ApplyRequest):
    print(f"\n[Bridge] Received native receipts for proposal {req.proposal_id}: {req.apply_status} / {req.editor_validation_status}")
    activity_monitor.record(
        level="info" if req.apply_status == "success" else "error",
        source="plugin_bridge",
        event_type="apply_proposal",
        message="Plugin apply callback received",
        details={
            "proposal_id": req.proposal_id,
            "apply_status": req.apply_status,
            "editor_validation_status": req.editor_validation_status,
            "receipts_count": len(req.native_receipts),
        },
    )
    for r in req.native_receipts:
        print(f"  - {r}")

    proposal = run_store.load_proposal(req.proposal_id)
    proposal_payload = proposal.action_batch_json if proposal else "{}"

    import sqlite3
    run_id = str(uuid.uuid4())
    try:
        with sqlite3.connect(run_store.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT run_id, state_json FROM runs ORDER BY updated_at DESC LIMIT 1')
            row = c.fetchone()
            if row:
                run_id = row[0]
                state = RunState.model_validate_json(row[1])
                state.status = RunStatus.COMPLETED if req.apply_status == "success" else RunStatus.FAILED
                state.current_node = OrchestrationNode.DONE
                
                state.context_snapshot["apply_receipts"] = req.native_receipts
                state.context_snapshot["proposal_payload"] = proposal_payload
                state.validation_report = None
                
                run_store.update_run(state)
    except Exception as e:
        print(f"[Bridge] Could not update RunState: {e}")
            
    return {
        "run_id": run_id,
        "status": req.apply_status,
        "validation_result": req.editor_validation_status,
        "native_receipts": req.native_receipts,
        "touched_files": [],
        "touched_nodes": []
    }
