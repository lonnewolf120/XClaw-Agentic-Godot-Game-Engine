from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts.run_state import RunMode, RunStatus
from orchestration.game_creation import GameCreationEngine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = PROJECT_ROOT / "benchmarks" / "prompt_corpus_v2.txt"
RESULTS_DIR = PROJECT_ROOT / "benchmarks" / "results"


@dataclass
class BenchmarkPromptResult:
    prompt: str
    status: str
    duration_seconds: float
    retry_count: int
    selected_template: str
    generated_asset_requests: int
    missing_categories: int
    failure_class: str | None


def _load_prompts(path: Path) -> list[str]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    return [line for line in lines if line and not line.startswith("#")]


def _extract_bundle_metrics(run_bundle_path: Path) -> tuple[str, int, int]:
    if not run_bundle_path.exists():
        return "unknown", 0, 0
    try:
        payload = json.loads(run_bundle_path.read_text(encoding="utf-8"))
        selected_template = payload.get("project_spec", {}).get("selected_template", "unknown")
        asset_plan = payload.get("asset_plan") or {}
        generated_count = len(asset_plan.get("generated_asset_requests", []))
        missing_count = len(asset_plan.get("missing_categories", []))
        return selected_template, generated_count, missing_count
    except Exception:
        return "unknown", 0, 0


def run_benchmark(
    prompts: list[str],
    *,
    with_export: bool,
    strict_export: bool,
    subset: int | None = None,
) -> list[BenchmarkPromptResult]:
    engine = GameCreationEngine(workspace_root=PROJECT_ROOT)

    results: list[BenchmarkPromptResult] = []
    
    if subset:
        prompts = prompts[:subset]
        
    for idx, prompt in enumerate(prompts, 1):
        print(f"[{idx}/{len(prompts)}] Running prompt: {prompt[:60]}...")
        start_time = time.time()
        result = engine.create_from_prompt(
            prompt=prompt,
            mode=RunMode.STANDALONE,
            enable_export=with_export,
            strict_export=strict_export,
        )
        duration = round(time.time() - start_time, 2)
        
        selected_template, generated_count, missing_count = _extract_bundle_metrics(result.run_bundle_path)
        
        failure_class = None
        status_val = result.status.value if hasattr(result.status, "value") else str(result.status)
        if status_val != RunStatus.COMPLETED.value:
            if result.validation_report and result.validation_report.summary:
                failure_class = result.validation_report.summary
            elif result.export_result and not result.export_result.success:
                failure_class = result.export_result.error_summary or "export_failed"
            else:
                failure_class = "internal_error"
                
        results.append(
            BenchmarkPromptResult(
                prompt=prompt,
                status=status_val,
                duration_seconds=duration,
                retry_count=result.retry_count,
                selected_template=selected_template,
                generated_asset_requests=generated_count,
                missing_categories=missing_count,
                failure_class=failure_class,
            )
        )

    return results


def _write_results(results: list[BenchmarkPromptResult], args: argparse.Namespace) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    completed = sum(1 for item in results if item.status == RunStatus.COMPLETED.value)
    pass_rate = completed / len(results) if results else 0.0
    templates = Counter(item.selected_template for item in results)
    
    failure_taxonomy = Counter(item.failure_class for item in results if item.failure_class)
    avg_duration = sum(item.duration_seconds for item in results) / len(results) if results else 0.0
    avg_retries = sum(item.retry_count for item in results) / len(results) if results else 0.0

    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "settings": {
            "with_export": args.with_export,
            "strict_export": args.strict_export,
        },
        "summary": {
            "total_prompts": len(results),
            "completed": completed,
            "pass_rate": round(pass_rate, 4),
            "avg_duration_seconds": round(avg_duration, 2),
            "avg_retries": round(avg_retries, 2),
            "failure_taxonomy": dict(failure_taxonomy),
            "template_coverage": len(templates),
            "template_counts": dict(templates),
        },
        "results": [asdict(item) for item in results],
    }

    output_path = RESULTS_DIR / f"full_latest_{timestamp}.json"
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (RESULTS_DIR / "full_latest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run full regression benchmark on game creation pipeline")
    parser.add_argument("--corpus", default=str(DEFAULT_CORPUS), help="Path to prompt corpus")
    parser.add_argument("--with-export", action="store_true", help="Enable export while benchmarking")
    parser.add_argument("--strict-export", action="store_true", help="Fail run if export fails")
    parser.add_argument("--subset", type=int, default=None, help="Run only the first N prompts (for testing)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prompts = _load_prompts(Path(args.corpus))
    
    print(f"Loaded {len(prompts)} prompts from {args.corpus}")

    results = run_benchmark(
        prompts,
        with_export=args.with_export,
        strict_export=args.strict_export,
        subset=args.subset,
    )

    output_path = _write_results(results, args)
    completed = sum(1 for item in results if item.status == RunStatus.COMPLETED.value)
    print(f"benchmark_completed={completed}/{len(results)}")
    print(f"benchmark_pass_rate={completed / len(results):.2%}")
    print(f"benchmark_results={output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
