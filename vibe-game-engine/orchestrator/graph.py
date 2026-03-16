import logging
from typing import Dict, Any

from contracts.run_state import RunState, RunStatus, OrchestrationNode
from contracts.validation import ValidationReport
from store.run_store import RunStore
from store.cloud_storage import ArtifactStore
from generators.scaffold_builder import ScaffoldBuilder
from validation.headless_runner import HeadlessValidator
from agents.planner import PlannerAgent
from agents.debugger import DebuggerAgent
from contracts.godot_patch import PatchOp
import os
import logging

logger = logging.getLogger(__name__)

class SkeletonGraph:
    """Minimal stage transitions for Phase 0 deterministic flow without real LLMs."""
    def __init__(self, store: RunStore):
        self.store = store
        self.gcs = ArtifactStore()
        
    def step_intake(self, run_id: str):
        state = self.store.load_run(run_id)
        if not state: 
            return None
        
        logger.info(f"[{run_id}] Executing INTAKE")
        # Logic: Read prompt -> transition to PLANNING
        state.current_node = OrchestrationNode.PLANNING
        state.status = RunStatus.PLANNING
        self.store.update_run(state)
        return state

    def step_planning(self, run_id: str):
        state = self.store.load_run(run_id)
        if not state: 
            return None
        
        logger.info(f"[{run_id}] Executing PLANNING")
        
        planner = PlannerAgent()
        plan_message = planner.plan(state.prompt)
        state.plan = plan_message
        
        self.store.append_message(
            run_id=run_id,
            message_type="plan",
            payload=plan_message
        )

        state.current_node = OrchestrationNode.BUILDING
        state.status = RunStatus.VALIDATING
        self.store.update_run(state)
        return state

    def step_building(self, run_id: str):
        state = self.store.load_run(run_id)
        if not state: 
            return None
        
        logger.info(f"[{run_id}] Executing BUILDING")
        
        # Read from plan
        archetype = "platformer"
        if state.plan and state.plan.archetype:
            archetype = state.plan.archetype

        # Logic: Generate Godot script/resources
        builder = ScaffoldBuilder(state.workspace_dir)
        manifest = builder.build_archetype(archetype)
        
        # Keep track of artifacts
        for rel_path, full_path in manifest.items():
            state.artifacts.artifact_paths.append(full_path)
            self.store.append_artifact(
                run_id=run_id,
                artifact_type="scaffold_file",
                path=full_path,
                metadata={"archetype": "platformer", "file": rel_path}
            )

        # Zip and push the newly scaffolded workspace context to GCS
        # so any scaled Cloud Run job or Validation container can read it.
        self.gcs.upload_workspace(run_id, state.workspace_dir)

        state.current_node = OrchestrationNode.VALIDATION
        state.status = RunStatus.VALIDATING
        self.store.update_run(state)
        return state

    def step_validating(self, run_id: str):
        state = self.store.load_run(run_id)
        if not state: 
            return None
        
        logger.info(f"[{run_id}] Executing VALIDATING")
        
        # Ensure workspace is hydrated locally if we are running in a stateless container
        self.gcs.download_workspace(run_id, state.workspace_dir)

        # Logic: Execute Tier 1-3 validation (Headless smoke passing)
        
        # Check if Docker is available, otherwise use local Godot (fallback for Phase 0 local testing)
        # We default use_docker to False locally if we don't have docker running, but try standard.
        # Let's try use_docker=False initially to use a local or fallback, but the contract says containerized.
        validator = HeadlessValidator(use_docker=False) 
        # (Assuming local godot might be in PATH. If using Docker, switch to True)
        
        report = validator.validate(state.workspace_dir)
        state.validation_report = report
        
        if report.success:
            state.status = RunStatus.COMPLETED
            state.current_node = OrchestrationNode.DONE
        else:
            if state.retry_count < state.max_retries:
                state.status = RunStatus.DEBUGGING
                state.current_node = OrchestrationNode.DEBUG
            else:
                state.status = RunStatus.FAILED
                state.current_node = OrchestrationNode.DONE
                
            state.failure_reason = report.summary
        
        self.store.update_run(state)
        return state

    def step_debugging(self, run_id: str):
        state = self.store.load_run(run_id)
        if not state: return None
        
        logger.info(f"[{run_id}] Executing DEBUGGING (Attempt {state.retry_count + 1})")
        debugger = DebuggerAgent()
        
        try:
            debug_msg = debugger.debug(state)
            
            # Record patch trace conceptually
            self.store.append_message(
                run_id=run_id,
                message_type="debug_patch",
                payload=debug_msg
            )

            # Optional: Simple patch applier for Phase 1 could be here.
            # For now, deterministic step loop mock:
            state.retry_count += 1
            
            from contracts.run_state import RetryEvent
            import datetime
            state.retry_events.append(RetryEvent(
                attempt=state.retry_count,
                node=OrchestrationNode.DEBUG,
                reason=state.failure_reason or "Unknown",
                timestamp_utc=datetime.datetime.utcnow().isoformat() + "Z"
            ))
            
            # Send back to validation
            state.status = RunStatus.VALIDATING
            state.current_node = OrchestrationNode.VALIDATION
            
        except Exception as e:
            logger.error(f"Debugger failed: {e}")
            state.status = RunStatus.FAILED
            state.failure_reason = f"Debugger error: {str(e)}"
            state.current_node = OrchestrationNode.DONE

        self.store.update_run(state)
        return state

    def step_post_commit_refresh(self, run_id: str):
        """Re-indexes the project graph after successful patches/builds."""
        state = self.store.load_run(run_id)
        if not state: return None
        
        logger.info(f"[{run_id}] Executing POST_COMMIT_REFRESH")
        
        from store.project_graph import ProjectGraphStore
        from store.project_graph_parser import ProjectGraphParser
        import os
        
        db_path = os.path.join(state.workspace_dir, "project_graph.db")
        store = ProjectGraphStore(db_path)
        parser = ProjectGraphParser(state.workspace_dir, store)
        
        # Clean up stale chunks before adding new ones
        valid_files = []
        for root, _, files in os.walk(state.workspace_dir):
            if ".godot" in root: continue
            for f in files:
                rel_path = f"res://{os.path.relpath(os.path.join(root, f), state.workspace_dir).replace(os.sep, '/')}"
                valid_files.append(rel_path)
                
        store.cleanup_stale_chunks("default", valid_files)
        
        # Re-parse changed files (Parser uses hash-based invalidation under the hood)
        parser.sync_project()
        
        return state

    def run_all(self, run_id: str):
        logger.info(f"Starting orchestration for: {run_id}")
        self.step_intake(run_id)
        self.step_planning(run_id)
        self.step_building(run_id)
        
        # Validation <-> Debug loop
        state = self.step_validating(run_id)
        while state and state.current_node == OrchestrationNode.DEBUG:
            state = self.step_debugging(run_id)
            if state and state.current_node == OrchestrationNode.VALIDATION:
                state = self.step_validating(run_id)

        if state and state.status == RunStatus.COMPLETED:
            self.step_post_commit_refresh(run_id)

        logger.info(f"Completed orchestration for: {run_id} with final status: {state.status.value if state else 'unknown'}")
