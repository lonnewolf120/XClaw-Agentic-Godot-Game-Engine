import os
import sys
import argparse
from store.project_graph import ProjectGraphStore
from store.project_graph_parser import ProjectGraphParser
from agents.retrieval_orchestrator import RetrievalOrchestrator

BENCHMARK_QUERIES = [
    ("make player jump higher", ["res://player/player.gd"]),
    ("connect damage signal to HUD", ["res://player/player.tscn"]),
    ("change enemy speed in runner", []),
    ("modify dialogue progression", ["res://ui/dialogue.gd"])
]

def run_benchmark(workspace_path: str):
    print(f"--- Starting Retrieval Benchmark in {workspace_path} ---")
    store = ProjectGraphStore("benchmark_graph.db")
    parser = ProjectGraphParser(workspace_path, store)
    
    print("1. Parsing project graph (FTS + Metadata + Edges)...")
    parser.sync_project()
    
    orchestrator = RetrievalOrchestrator(store)
    
    successes = 0
    
    for query, hints in BENCHMARK_QUERIES:
        print(f"\n[Query]: '{query}' (Hints: {hints})")
        result = orchestrator.retrieve_for_prompt(query, hints)
        
        chunks_used = result.get('chunks_used', 0)
        sources = result.get('sources', {})
        
        print(f"  -> Retreived {chunks_used} chunks.")
        print(f"  -> Sources: Lexical({sources.get('lexical')}), Graph({sources.get('graph')}), Vector({sources.get('vector')})")
        
        # Simple heuristic for success: we actually found something
        if chunks_used > 0:
            successes += 1
            print("  -> Result: PASS")
        else:
             print("  -> Result: FAIL (No context found)")

    print(f"\n--- Benchmark Complete: {successes}/{len(BENCHMARK_QUERIES)} queries successful ---")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=str, required=True, help="Path to Godot project workspace")
    args = parser.parse_args()
    run_benchmark(args.workspace)
