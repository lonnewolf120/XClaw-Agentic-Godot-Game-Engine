import sqlite3
import json
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, StrictStr

from store.run_store import RunStore
from workspace.workspace_runner import WorkspaceRunner
from workers.queue import queue_instance

router = APIRouter(prefix="/runs", tags=["Runs"])

store = RunStore()
ws_runner = WorkspaceRunner()
logger = logging.getLogger(__name__)

class CreateRunRequest(BaseModel):
    prompt: StrictStr

@router.post("")
def create_run(request: CreateRunRequest):
    """
    Creates an isolated workspace, persists initial RunState, 
    and enqueues the Intake orchestration stage.
    """
    try:
        workspace_path = ws_runner.create_workspace()
        run_state = store.create_run(request.prompt, workspace_path)
        
        # Enqueue the run to start processing in the background (orchestration)
        queue_instance.enqueue_orchestration(run_state.run_id, "START_GRAPH", {})

        return {"run_id": run_state.run_id, "status": run_state.status.value, "node": run_state.current_node.value}

    except Exception as e:
        logger.error(f"Failed to create run: {e}")
        raise HTTPException(status_code=500, detail="Internal server error storing run.")

@router.get("/{run_id}")
def get_run(run_id: str):
    """Return run summary schema."""
    run_state = store.load_run(run_id)
    if not run_state:
        raise HTTPException(status_code=404, detail="Run not found.")
    
    return {
        "run_id": run_state.run_id,
        "status": run_state.status.value,
        "current_node": run_state.current_node.value,
        "retry_count": run_state.retry_count,
        "workspace_dir": run_state.workspace_dir
    }

@router.get("/{run_id}/messages")
def get_run_messages(run_id: str):
    with sqlite3.connect(store.db_path) as conn:
        c = conn.cursor()
        c.execute('SELECT message_type, payload_json, created_at FROM run_messages WHERE run_id = ? ORDER BY created_at ASC', (run_id,))
        rows = c.fetchall()
        
        messages = [{"type": r[0], "payload": json.loads(r[1]), "timestamp": r[2]} for r in rows]
        return {"run_id": run_id, "messages": messages}

@router.get("/{run_id}/artifacts")
def get_run_artifacts(run_id: str):
    with sqlite3.connect(store.db_path) as conn:
        c = conn.cursor()
        c.execute('SELECT artifact_type, path, metadata_json, created_at FROM run_artifacts WHERE run_id = ? ORDER BY created_at ASC', (run_id,))
        rows = c.fetchall()
        
        artifacts = [{"type": r[0], "path": r[1], "metadata": json.loads(r[2]), "timestamp": r[3]} for r in rows]
        return {"run_id": run_id, "artifacts": artifacts}

@router.post("/{run_id}/cancel")
def cancel_run(run_id: str):
    run_state = store.load_run(run_id)
    if not run_state:
        raise HTTPException(status_code=404, detail="Run not found.")
    
    # Mark state as cancelled/failed conceptually. Real implementation will halt worker pull.
    run_state.status = "failed"
    run_state.failure_reason = "Cancelled by user"
    store.update_run(run_state)

    return {"run_id": run_id, "status": "cancelled"}
