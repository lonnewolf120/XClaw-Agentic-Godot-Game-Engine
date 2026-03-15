import logging
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, StrictStr
from typing import Dict, Any

from store.run_store import RunStore
from orchestrator.graph import SkeletonGraph

router = APIRouter(prefix="/internal/tasks", tags=["Internal Tasks"])
logger = logging.getLogger(__name__)

store = RunStore()

class CloudTaskPayload(BaseModel):
    run_id: StrictStr
    command: StrictStr
    payload: Dict[str, Any]

@router.post("")
async def handle_cloud_task(task: CloudTaskPayload):
    """
    Receives an HTTP POST from Google Cloud Tasks (or local test client).
    This invokes the orchestrator synchronously on this Cloud Run instance.
    """
    logger.info(f"Received Cloud Task for run {task.run_id}, command {task.command}")
    
    graph = SkeletonGraph(store)
    
    try:
        if task.command == "START_GRAPH":
            # Just do full progression for prototype
            graph.step_intake(task.run_id)
            graph.step_planning(task.run_id)
            graph.step_building(task.run_id)
            # Validation is tricky because Cloud Run can't run Godot directly easily
            # unless it's a very big custom container. 
            # In Phase 0.5 we assume we dispatch this to the Validator Cloud Run Job,
            # or just execute it directly if we packaged Headless Godot in this very image.
            
            # For simplicity, just run step_validating and step_debugging here if it's the exact same Docker image,
            # or rely on the orchestrator to have spawned it as a Job.
            # Right now, step_validating tries to run HeadlessValidator
            report = graph.step_validating(task.run_id)
            # If we need debugging
            graph.step_debugging(task.run_id)
            return {"status": "processed"}
            
        else:
            logger.warning(f"Unknown command: {task.command}")
            return {"status": "ignored"}
            
    except Exception as e:
        logger.error(f"Error processing task {task.run_id}: {e}")
        # In Cloud Tasks, throwing an HTTP 500 triggers retry
        raise HTTPException(status_code=500, detail=str(e))
