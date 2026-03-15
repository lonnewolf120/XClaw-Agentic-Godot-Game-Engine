"""POC-003: Strict-export matrix for 4 templates.

Runs the game creation pipeline with strict_export=True for Racing, City Builder,
FPS, and Base 2D Platformer control.  Outputs structured JSON report and summary
table.

Usage:
    python scripts/strict_export_matrix.py [--godot-exe docker:barichello/godot-ci:4.6.1]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure vibe-game-engine is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestration.game_creation import GameCreationEngine

MATRIX_TEMPLATES: list[dict[str, str]] = [
    {
        "label": "Racing (Kenney)",
        "prompt": "Create an arcade racing game with vehicle controls and track.",
    },
    {
        "label": "City Builder (Kenney)",
        "prompt": "Build a 3D city builder with building placement and removal.",
    },
    {
        "label": "FPS (Kenney)",
        "prompt": "Create a first person shooter with one weapon and enemies.",
    },
    {
        "label": "Base 2D Platformer (Control)",
        "prompt": "Create a tiny 2D platformer with jump and one enemy.",
    },
]


def run_matrix(godot_exe: str | None = None) -> dict:
    root = Path(__file__).resolve().parents[1]
    engine = GameCreationEngine(workspace_root=root)

    results: list[dict] = []

    for entry in MATRIX_TEMPLATES:
        label = entry["label"]
        prompt = entry["prompt"]
        print(f"\n{'='*60}")
        print(f"  Template: {label}")
        print(f"  Prompt:   {prompt}")
        print(f"{'='*60}")

        try:
            result = engine.create_from_prompt(
                prompt,
                enable_export=True,
                strict_export=True,
                godot_exe=godot_exe,
                progress_callback=lambda msg: print(f"  {msg}"),
            )
            outcome = {
                "label": label,
                "prompt": prompt,
                "status": result.status.value,
                "export_success": result.export_result.success if result.export_result else False,
                "error_summary": (
                    result.export_result.error_summary
                    if result.export_result and result.export_result.error_summary
                    else result.validation_report.summary
                ),
                "preset_bootstrapped": result.preset_bootstrapped,
                "run_bundle": str(result.run_bundle_path),
                "gate_d_log_paths": result.gate_d_log_paths,
                "gate_e_log_paths": result.gate_e_log_paths,
            }
        except Exception as exc:
            outcome = {
                "label": label,
                "prompt": prompt,
                "status": "exception",
                "export_success": False,
                "error_summary": str(exc),
                "preset_bootstrapped": False,
                "run_bundle": "",
                "gate_d_log_paths": [],
                "gate_e_log_paths": [],
            }

        results.append(outcome)
        status_icon = "\u2705" if outcome["status"] == "completed" and outcome["export_success"] else "\u274c"
        print(f"\n  Result: {status_icon} {outcome['status']}  export={outcome['export_success']}")

    # --- Summary ---
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "completed" and r["export_success"])
    kenney_results = [r for r in results if "Kenney" in r["label"]]
    kenney_passed = sum(1 for r in kenney_results if r["status"] == "completed" and r["export_success"])

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_templates": total,
        "total_passed": passed,
        "kenney_total": len(kenney_results),
        "kenney_passed": kenney_passed,
        "acceptance_met": passed >= 3 and kenney_passed >= 2,
        "results": results,
    }

    # Write report
    report_dir = root / "benchmarks" / "results"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "strict_export_matrix.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Print summary table
    print(f"\n\n{'='*70}")
    print("  STRICT-EXPORT MATRIX RESULTS")
    print(f"{'='*70}")
    print(f"  {'Template':<35} {'Status':<12} {'Export':<8} {'Preset Boot'}")
    print(f"  {'-'*35} {'-'*12} {'-'*8} {'-'*11}")
    for r in results:
        status_icon = "\u2705" if r["status"] == "completed" and r["export_success"] else "\u274c"
        print(
            f"  {r['label']:<35} {status_icon} {r['status']:<10} "
            f"{'pass' if r['export_success'] else 'FAIL':<8} "
            f"{'yes' if r['preset_bootstrapped'] else 'no'}"
        )
    print(f"\n  Total: {passed}/{total}  Kenney: {kenney_passed}/{len(kenney_results)}")
    print(f"  Acceptance (>=3/4, >=2 Kenney): {'PASS' if report['acceptance_met'] else 'FAIL'}")
    print(f"  Report: {report_path}")
    print(f"{'='*70}\n")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="POC-003 strict export matrix")
    parser.add_argument("--godot-exe", default=None, help="Godot executable or docker:image")
    args = parser.parse_args()
    run_matrix(godot_exe=args.godot_exe)


if __name__ == "__main__":
    main()
