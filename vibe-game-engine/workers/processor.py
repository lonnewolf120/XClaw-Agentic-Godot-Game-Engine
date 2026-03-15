import time
import logging
import threading
from typing import Optional

from store.run_store import RunStore
from workers.queue import queue_instance, LocalQueue
from orchestrator.graph import SkeletonGraph

logger = logging.getLogger(__name__)

class WorkerProcessor:
    """Consumes the LocalQueue and runs the SkeletonGraph pipeline in a background thread."""
    def __init__(self, store: RunStore, queue: LocalQueue):
        self.store = store
        self.queue = queue
        self.graph = SkeletonGraph(store)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        logger.info("Starting worker processor thread...")
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        logger.info("Stopping worker processor thread...")
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run_loop(self):
        while not self._stop_event.is_set():
            task = self.queue.get_orchestration_task()
            if task:
                try:
                    logger.info(f"Processing task: {task.task_id} for run: {task.run_id}")
                    cmd = task.payload.get("command")
                    
                    if cmd == "START_GRAPH":
                        # Execute full phase 0 dummy deterministic pipeline
                        self.graph.run_all(task.run_id)
                    else:
                        logger.warning(f"Unknown command: {cmd}")
                        
                except Exception as e:
                    logger.error(f"Error processing task {task.task_id}: {e}", exc_info=True)
                    # Mark run as failed
                    state = self.store.load_run(task.run_id)
                    if state:
                        from contracts.run_state import RunStatus
                        state.status = RunStatus.FAILED
                        state.failure_reason = str(e)
                        self.store.update_run(state)
            else:
                time.sleep(1.0) # avoid tight loop
