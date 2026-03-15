import os
import json
import logging
from typing import Dict, Any

try:
    from google.cloud import tasks_v2
    CLOUD_TASKS_AVAILABLE = True
except ImportError:
    CLOUD_TASKS_AVAILABLE = False

logger = logging.getLogger(__name__)

class CloudTasksQueue:
    """
    Phase 0.5 GCP-native queue dispatch abstraction.
    Sends task execution to the worker HTTP endpoint hosted on Cloud Run.
    """
    def __init__(self, project: str, location: str, orchestrator_queue: str, worker_url: str):
        self.project = project
        self.location = location
        self.queue_id = orchestrator_queue
        self.worker_url = worker_url
        if CLOUD_TASKS_AVAILABLE:
            self.client = tasks_v2.CloudTasksClient()
            self.parent = self.client.queue_path(self.project, self.location, self.queue_id)
        else:
            logger.warning("google-cloud-tasks not installed. CloudTasksQueue won't work.")

    def enqueue_orchestration(self, run_id: str, command: str, payload: dict):
        if not CLOUD_TASKS_AVAILABLE:
            logger.error("google-cloud-tasks library missing.")
            return None

        # Build the Cloud Task payload targeted at our async worker service
        task_payload = {
            "run_id": run_id,
            "command": command,
            "payload": payload
        }
        
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{self.worker_url}/internal/async",
                "headers": {"Content-type": "application/json"},
                "body": json.dumps(task_payload).encode()
            }
        }

        try:
            response = self.client.create_task(
                request={"parent": self.parent, "task": task}
            )
            logger.info(f"Dispatched task to Cloud Tasks: {response.name}")
            return response.name
        except Exception as e:
            logger.error(f"Failed to submit Cloud Task: {e}")
            raise
