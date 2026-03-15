from __future__ import annotations

import json

from scripts import qa_benchmark
from contracts.run_state import RunStatus


def test_qa_benchmark_hits_success_threshold(tmp_path) -> None:
    results = qa_benchmark.run_benchmark([f"prompt {i}" for i in range(10)], workspace_root=tmp_path)
    successes = sum(1 for r in results if r.success)
    assert successes >= 8


def test_load_prompt_corpus_ignores_comments_and_blanks(tmp_path) -> None:
    corpus = tmp_path / "prompts.txt"
    corpus.write_text("# header\n\nalpha\n beta  \n", encoding="utf-8")

    prompts = qa_benchmark.load_prompt_corpus(corpus)
    assert prompts == ["alpha", "beta"]


def test_benchmark_writes_latest_and_history(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(qa_benchmark, "BENCHMARK_RESULTS_DIR", tmp_path / "results")

    results = qa_benchmark.run_benchmark([f"prompt {i}" for i in range(10)], workspace_root=tmp_path)
    qa_benchmark._write_benchmark_results(results)

    latest_path = tmp_path / "results" / "latest.json"
    history_path = tmp_path / "results" / "history.jsonl"
    assert latest_path.exists()
    assert history_path.exists()

    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest["summary"]["total_prompts"] == 10
    assert len(latest["results"]) == 10

    history_lines = [line for line in history_path.read_text(encoding="utf-8").splitlines() if line]
    assert len(history_lines) == 1


def test_benchmark_emits_escalation_paths_for_needs_human(tmp_path, monkeypatch) -> None:
    results = qa_benchmark.run_benchmark([f"prompt {i}" for i in range(10)], workspace_root=tmp_path)
    escalations = [item for item in results if item.final_status == RunStatus.NEEDS_HUMAN]

    assert len(escalations) == 2
    assert all(item.escalation_ticket_path for item in escalations)
