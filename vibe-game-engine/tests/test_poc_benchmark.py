from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.poc_benchmark import _load_prompts


def test_poc_prompt_corpus_has_20_prompts() -> None:
    corpus_path = Path(__file__).resolve().parents[1] / "benchmarks" / "prompt_corpus_poc_v1.txt"
    prompts = _load_prompts(corpus_path)
    assert len(prompts) == 20
