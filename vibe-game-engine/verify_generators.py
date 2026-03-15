import sys
import logging
import os
from pathlib import Path

# Add to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from store.run_store import RunStore
from workspace.workspace_runner import WorkspaceRunner
from orchestrator.graph import SkeletonGraph

logging.basicConfig(level=logging.INFO)

def test_archetype(prompt: str, expected_type: str):
    print(f"\n--- Testing Archetype: {expected_type} ---")
    store = RunStore('vibe_runs.db')
    workspace = WorkspaceRunner('runs')
    graph = SkeletonGraph(store)

    workspace_path = workspace.create_workspace()
    state = store.create_run(prompt, workspace_path)
    run_id = state.run_id
    
    print(f"Created RUN: {run_id} in {workspace_path}")
    graph.run_all(run_id)

    final_state = store.load_run(run_id)
    print(f"Final Status: {final_state.status.value}")
    
    assert final_state.validation_report is not None, "Missing validation report"
    
    report = final_state.validation_report
    print(f"Validation Report Summary: {report.summary}")
    print(f"Validation Success: {report.success}")
    if not report.success:
        print(f"Failed Tier: {report.failed_tier}")
        if report.issues:
            print(f"Issue: {report.issues[0].message}")
    
    generated_dir = Path(workspace_path) / "generated"
    
    assert (generated_dir / "project.godot").exists(), "Missing project.godot"
    assert (generated_dir / "assets").exists(), "Missing assets folder"
    
    if expected_type in ["platformer", "runner"]:
        assert (generated_dir / "scenes/player.tscn").exists(), "Missing player scene"
        assert (generated_dir / "scripts/player.gd").exists(), "Missing player script"
    elif expected_type == "dialogue":
        assert (generated_dir / "scripts/dialogue_manager.gd").exists(), "Missing dialogue manager"
        
    print(f"Directory structure validated for {expected_type}.")
    return run_id

if __name__ == "__main__":
    test_archetype("Make a 2D platformer game", "platformer")
    test_archetype("Make an endless runner game", "runner")
    test_archetype("Make a dialogue narrative story.", "dialogue")
    print("\nALL ARCHETYPES PASSED.")
