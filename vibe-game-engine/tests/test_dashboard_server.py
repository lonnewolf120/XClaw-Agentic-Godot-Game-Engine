from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import scripts.dashboard_server as dashboard_server


def test_build_overview_includes_expected_sections(tmp_path, monkeypatch) -> None:
    project = tmp_path / "project"
    (project / "benchmarks" / "results").mkdir(parents=True, exist_ok=True)
    (project / "runs").mkdir(parents=True, exist_ok=True)

    (project / "benchmarks" / "results" / "latest.json").write_text(
        json.dumps({"summary": {"success_rate": 0.81, "total_prompts": 42}}),
        encoding="utf-8",
    )
    (project / "runs" / "needs_human_queue.jsonl").write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(dashboard_server, "PROJECT_ROOT", project)
    monkeypatch.setattr(dashboard_server, "COMMAND_LOG_DIR", project / "runs" / "dashboard_commands")

    overview = dashboard_server.build_overview()
    assert "kpis" in overview
    assert "agents" in overview
    assert "commands" in overview
    assert overview["kpis"]["benchmark_total_prompts"] == 42
    assert overview["kpis"]["needs_human_queue_items"] == 1


def test_commands_registry_has_run_benchmark() -> None:
    assert "run_benchmark" in dashboard_server.COMMANDS