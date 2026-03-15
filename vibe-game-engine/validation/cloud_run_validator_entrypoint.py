import os
import sys
import logging
import json
from pathlib import Path

# Adjust path if run as module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validation.headless_runner import HeadlessValidator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    """
    Entrypoint for a managed Cloud Run Job doing headless validation.
    Reads workspace path and run_id from environment variables.
    """
    workspace_path = os.environ.get("WORKSPACE_PATH")
    run_id = os.environ.get("RUN_ID")

    if not workspace_path:
        logger.error("WORKSPACE_PATH environment variable is missing.")
        sys.exit(1)

    logger.info(f"Starting cloud run validator for {run_id} at {workspace_path}")
    
    # In a Cloud Run Job environment, we already ARE the container, 
    # so we shouldn't use Docker to call another Docker container.
    # use_docker=False means run local `godot` binary directly.
    validator = HeadlessValidator(use_docker=False)
    
    report = validator.validate(workspace_path)
    
    # Normally this would be written back to Cloud Storage or Cloud SQL.
    # For Phase 0.5 stub, we log it so we can read it.
    output_meta = os.path.join(workspace_path, f"validation_{run_id}.json")
    with open(output_meta, "w") as f:
        f.write(report.model_dump_json())

    logger.info(f"Validation finished. Success: {report.success}")

if __name__ == "__main__":
    main()
