from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts.run_state import RunMode, RunStatus
from orchestration.game_creation import GameCreationEngine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = PROJECT_ROOT / "benchmarks" / "prompt_corpus_poc_v1.txt"
RESULTS_DIR = PROJECT_ROOT / "benchmarks" / "results"


@dataclass
class PocPromptResult:
    prompt: str
    status: str
    retry_count: int
    selected_template: str
    generated_asset_requests: int
    missing_categories: int


def _load_prompts(path: Path) -> list[str]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    return [line for line in lines if line and not line.startswith("#")]


def _extract_bundle_metrics(run_bundle_path: Path) -> tuple[str, int, int]:
    payload = json.loads(run_bundle_path.read_text(encoding="utf-8"))
    selected_template = payload.get("project_spec", {}).get("selected_template", "unknown")
    asset_plan = payload.get("asset_plan") or {}
    generated_count = len(asset_plan.get("generated_asset_requests", []))
    missing_count = len(asset_plan.get("missing_categories", []))
    return selected_template, generated_count, missing_count


def run_poc_benchmark(
    prompts: list[str],
    *,
    with_export: bool,
    strict_export: bool,
    pass_rate_target: float,
    min_template_coverage: int,
) -> tuple[list[PocPromptResult], bool]:
    engine = GameCreationEngine(workspace_root=PROJECT_ROOT)

    results: list[PocPromptResult] = []
    for prompt in prompts:
        result = engine.create_from_prompt(
            prompt=prompt,
            mode=RunMode.STANDALONE,
            enable_export=with_export,
            strict_export=strict_export,
        )
        selected_template, generated_count, missing_count = _extract_bundle_metrics(result.run_bundle_path)
        results.append(
            PocPromptResult(
                prompt=prompt,
                status=result.status.value if hasattr(result.status, "value") else str(result.status),
                retry_count=result.retry_count,
                selected_template=selected_template,
                generated_asset_requests=generated_count,
                missing_categories=missing_count,
            )
        )

    completed = sum(1 for item in results if item.status == RunStatus.COMPLETED.value)
    pass_rate = completed / len(results) if results else 0.0
    template_coverage = len({item.selected_template for item in results})

    gate_pass = pass_rate >= pass_rate_target and template_coverage >= min_template_coverage
    return results, gate_pass


def _write_results(results: list[PocPromptResult], gate_pass: bool, args: argparse.Namespace) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    completed = sum(1 for item in results if item.status == RunStatus.COMPLETED.value)
    pass_rate = completed / len(results) if results else 0.0
    templates = Counter(item.selected_template for item in results)

    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "gate_pass": gate_pass,
        "settings": {
            "with_export": args.with_export,
            "strict_export": args.strict_export,
            "pass_rate_target": args.pass_rate_target,
            "min_template_coverage": args.min_template_coverage,
        },
        "summary": {
            "total_prompts": len(results),
            "completed": completed,
            "pass_rate": round(pass_rate, 4),
            "template_coverage": len(templates),
            "template_counts": dict(templates),
        },
        "results": [asdict(item) for item in results],
    }

    output_path = RESULTS_DIR / f"poc_latest_{timestamp}.json"
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (RESULTS_DIR / "poc_latest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PoC benchmark gate on game creation pipeline")
    parser.add_argument("--corpus", default=str(DEFAULT_CORPUS), help="Path to prompt corpus")
    parser.add_argument("--with-export", action="store_true", help="Enable export while benchmarking")
    parser.add_argument("--strict-export", action="store_true", help="Fail run if export fails")
    parser.add_argument("--pass-rate-target", type=float, default=0.8, help="Minimum pass rate target")
    parser.add_argument("--min-template-coverage", type=int, default=3, help="Minimum distinct templates used")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prompts = _load_prompts(Path(args.corpus))
    if len(prompts) != 20:
        raise ValueError(f"PoC corpus must contain exactly 20 prompts, found {len(prompts)}")

    results, gate_pass = run_poc_benchmark(
        prompts,
        with_export=args.with_export,
        strict_export=args.strict_export,
        pass_rate_target=args.pass_rate_target,
        min_template_coverage=args.min_template_coverage,
    )

    output_path = _write_results(results, gate_pass, args)
    completed = sum(1 for item in results if item.status == RunStatus.COMPLETED.value)
    print(f"poc_completed={completed}/{len(results)}")
    print(f"poc_gate_pass={gate_pass}")
    print(f"poc_results={output_path}")

    return 0 if gate_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
