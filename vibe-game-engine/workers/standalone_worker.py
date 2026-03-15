import os
import sys
import time
import logging

# Required so module can find itself if run as standalone module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from store.run_store import RunStore
from workers.queue import queue_instance
from workers.processor import WorkerProcessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting standalone background worker...")
    store = RunStore("vibe_runs.db") 
    worker = WorkerProcessor(store, queue_instance)
    
    worker.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupt received. Stopping worker...")
    finally:
        worker.stop()
        logger.info("Worker stopped.")

if __name__ == "__main__":
    main()
