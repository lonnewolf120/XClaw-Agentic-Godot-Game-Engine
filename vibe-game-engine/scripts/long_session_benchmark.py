import os
import argparse
import logging
from typing import List, Dict, Any
from agents.token_logger import TokenEconomicsLogger
from orchestrator.graph import SkeletonGraph
from store.run_store import RunStore
from store.project_graph_parser import ProjectGraphParser
from store.project_graph import ProjectGraphStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# A simulated user session interacting with the same Godot project over 25 steps.
# The mix includes mechanics tweaks, UI changes, asset drops, crash injections, and refactors.
SESSION_PROMPTS = [
    # Baseline setup
    "Generate a basic 2D platformer template with a player and one floor.",
    "Add a jump mechanic to the player.",
    "Make the player jump 20% higher.",
    "Spawn an enemy on the right side of the screen.",
    "Make the enemy pace left and right.",
    
    # Mechanic tweaks and small fixes
    "Reduce the enemy speed to 50.",
    "Add a signal that triggers when the player hits the enemy.",
    "Connect the hit signal to a print statement 'player hit'.",
    
    # Deliberate failure scenario 1 (missing script reference)
    "Attach 'hud_manager.gd' to the UI node. (Note: hud_manager.gd does not exist yet)",
    
    # Recovery
    "Create the 'hud_manager.gd' script and attach it to the UI node.",
    
    # Refactor
    "Move the jump logic into a separate physics function.",
    "Change the jump velocity variable name from 'jump_velocity' to 'JUMP_VELOCITY'.",
    
    # Asset drops
    "Import a new player sprite texture.",
    "Replace the player's CollisionShape2D with a CapsuleShape2D.",
    
    # Instancing
    "Create a new scene called 'Coin.tscn'.",
    "Instance the Coin scene 5 times randomly above the floor.",
    
    # Deletions / Index consistency
    "Delete the enemy pacing logic.",
    "Delete the Enemy node entirely.",
    
    # Deeper logic
    "When the player touches a Coin, destroy the Coin and increment a score variable.",
    "Print the score variable to the HUD script when it changes.",
    
    # Deliberate failure scenario 2 (runtime crash)
    "In the player script _process, call get_node('MissingNode').hide()",
    
    # Reconnect signals
    "Remove the debug print on enemy hit and instead reload the current scene.",
    
    # Architecture
    "Create a GlobalAutoload.gd script to store the high score.",
    "Add GlobalAutoload to the project settings.",
    
    # Final cleanup
    "Format all scripts to ensure consistent 4-space indentation."
]

def run_long_session(workspace_dir: str):
    logger.info(f"=== Starting Long-Session Benchmark Matrix (25 Prompts) ===")
    logger.info(f"Target Workspace: {workspace_dir}")
    
    os.makedirs(workspace_dir, exist_ok=True)
    db_path = os.path.join(workspace_dir, "vibe_runs.db")
    store = RunStore(db_path)
    graph = SkeletonGraph(store)
    
    # Reset economics logger for this session
    TokenEconomicsLogger.reset_session()
    
    session_stats = {
        "successes": 0,
        "failures": 0,
        "retries_invoked": 0,
        "rollbacks_invoked": 0
    }
    
    for idx, prompt in enumerate(SESSION_PROMPTS):
        logger.info(f"\n--- [Prompt {idx+1}/25] ---")
        logger.info(f"User: '{prompt}'")
        
        # 1. Create a new RunState for this prompt
        run_id = f"session_run_{idx+1:02d}"
        run_state = store.create_run(prompt=prompt, user_id="benchmark_user")
        run_state.workspace_dir = workspace_dir
        store.update_run(run_state)
        
        # 2. Execute the orchestration graph
        graph.run_all(run_state.run_id)
        
        # 3. Harvest metrics for this step
        final_state = store.load_run(run_state.run_id)
        
        if final_state.status.value == "COMPLETED":
            session_stats["successes"] += 1
            logger.info("Result: SUCCESS")
        else:
            session_stats["failures"] += 1
            logger.warning(f"Result: FAILED ({final_state.failure_reason})")
            
        if final_state.retry_count > 0:
            session_stats["retries_invoked"] += final_state.retry_count
            logger.info(f"Retries used: {final_state.retry_count}")
            
    # Session is complete. Generate Token Economics Report.
    logger.info("\n=== Session Complete. Generating Economic Proof Report ===")
    economics = TokenEconomicsLogger.get_session_summary()
    
    total_calls = economics["calls_made"]
    total_cost = economics["estimated_cost_usd"]
    
    success_rate = session_stats['successes'] / len(SESSION_PROMPTS) * 100
    cost_per_success = total_cost / session_stats['successes'] if session_stats['successes'] > 0 else 0
    
    logger.info(f"Total Prompts Executed : {len(SESSION_PROMPTS)}")
    logger.info(f"Success Rate           : {success_rate:.1f}%")
    logger.info(f"Total Retries Invoked  : {session_stats['retries_invoked']}")
    logger.info(f"Total LLM Calls Made   : {total_calls}")
    logger.info(f"Total Tokens Processed : {economics['tokens']['total_processed']:,}")
    logger.info(f"Total Session Cost     : ${total_cost:.4f}")
    logger.info(f"Avg Cost per Success   : ${cost_per_success:.4f}")
    
    # Dump ledger to disk for offline analysis
    ledger_path = os.path.join(workspace_dir, "token_ledger.json")
    TokenEconomicsLogger.dump_ledger(ledger_path)
    logger.info(f"Detailed token ledger saved to: {ledger_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=str, default="./tests/long_session", help="Path to temp workspace")
    args = parser.parse_args()
    run_long_session(args.workspace)
