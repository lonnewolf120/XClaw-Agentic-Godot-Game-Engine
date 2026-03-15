from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts.run_state import RunMode, RunStatus
from orchestration.game_creation import GameCreationEngine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a game project from a prompt")
    parser.add_argument("--prompt", required=True, help="Natural language game prompt")
    parser.add_argument(
        "--mode",
        default=RunMode.STANDALONE.value,
        choices=[item.value for item in RunMode],
        help="Run mode",
    )
    parser.add_argument(
        "--with-export",
        action="store_true",
        help="Run export and final manifest generation after successful project creation",
    )
    parser.add_argument(
        "--strict-export",
        action="store_true",
        help="Mark run as failed if export fails (requires --with-export)",
    )
    parser.add_argument(
        "--godot-exe",
        default=None,
        help="Optional Godot executable or docker:<image> override for export",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace_root = Path(__file__).resolve().parents[1]
    engine = GameCreationEngine(workspace_root=workspace_root)

    def _progress(line: str) -> None:
        print(line, flush=True)

    print("[CLI] create_game_from_prompt started", flush=True)
    print(f"[CLI] mode={args.mode} with_export={args.with_export} strict_export={args.strict_export}", flush=True)

    result = engine.create_from_prompt(
        prompt=args.prompt,
        mode=RunMode(args.mode),
        enable_export=args.with_export,
        strict_export=args.strict_export,
        godot_exe=args.godot_exe,
        progress_callback=_progress,
    )

    print(f"run_id={result.run_id}")
    print(f"project_dir={result.project_dir}")
    print(f"final_status={result.status}")
    print(f"retry_count={result.retry_count}")
    print(f"validation_summary={result.validation_report.summary}")
    print(f"export_success={result.export_result.success if result.export_result is not None else 'not_requested'}")
    print(f"final_manifest={result.final_manifest_path if result.final_manifest_path is not None else 'n/a'}")
    print(f"run_bundle={result.run_bundle_path}")
    print("[CLI] create_game_from_prompt finished", flush=True)

    return 0 if result.status == RunStatus.COMPLETED else 1


if __name__ == "__main__":
    raise SystemExit(main())
