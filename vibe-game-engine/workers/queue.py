import queue
import time
from typing import Callable, Any, Dict

# Very simple Phase 0 local queue abstraction. 
# Replaces complex Redis/Celery infra but can be swapped cleanly.

class TaskEnvelope:
    def __init__(self, task_id: str, run_id: str, payload: dict):
        self.task_id = task_id
        self.run_id = run_id
        self.payload = payload
        self.status = "pending"
        self.created_at = time.time()

class LocalQueue:
    def __init__(self):
        self.orchestration_queue = queue.Queue()
        self.execution_queue = queue.Queue()
    
    def enqueue_orchestration(self, run_id: str, command: str, payload: dict):
        task = TaskEnvelope(f"orch_{time.time()}", run_id, {"command": command, **payload})
        self.orchestration_queue.put(task)
        return task.task_id

    def enqueue_execution(self, run_id: str, command: str, payload: dict):
        task = TaskEnvelope(f"exec_{time.time()}", run_id, {"command": command, **payload})
        self.execution_queue.put(task)
        return task.task_id

    def get_orchestration_task(self):
        if not self.orchestration_queue.empty():
            return self.orchestration_queue.get()
        return None

    def get_execution_task(self):
        if not self.execution_queue.empty():
            return self.execution_queue.get()
        return None

# Singleton stub
queue_instance = LocalQueue()