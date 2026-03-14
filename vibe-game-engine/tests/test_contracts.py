from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts.export import ExportRequest, ExportTarget
from contracts.project_spec import (
    ComplexityTier,
    GameDimension,
    GameplayLoopSpec,
    PlatformTarget,
    ProjectSpec,
    ScopeGuardrails,
)
from contracts.run_state import RunMode, RunState


def test_run_state_rejects_extra_keys() -> None:
    with pytest.raises(ValidationError):
        RunState(
            run_id="run-001",
            prompt="build a game",
            mode=RunMode.STANDALONE,
            workspace_dir="runs/run-001",
            unexpected_field="nope",
        )


def test_run_state_rejects_type_mismatch() -> None:
    with pytest.raises(ValidationError):
        RunState(
            run_id="run-001",
            prompt="build a game",
            mode=RunMode.STANDALONE,
            workspace_dir="runs/run-001",
            retry_count="1",
        )


def test_project_spec_validates_required_fields() -> None:
    spec = ProjectSpec(
        run_id="run-001",
        title="Tiny Platformer",
        mode=RunMode.STANDALONE,
        game_dimension=GameDimension.TWO_D,
        complexity=ComplexityTier.SMALL,
        prompt_summary="A one level platformer",
        core_mechanics=["run", "jump"],
        target_platforms=[PlatformTarget.WINDOWS],
        gameplay_loop=GameplayLoopSpec(
            objective="Reach goal",
            win_condition="touch flag",
            fail_condition="fall off map",
            estimated_session_minutes=5,
        ),
        scope_guardrails=ScopeGuardrails(
            max_levels=1,
            max_playable_characters=1,
            multiplayer_enabled=False,
        ),
        selected_template="templates/base_2d_platformer",
    )

    assert spec.mode == RunMode.STANDALONE


def test_export_request_rejects_extra_key() -> None:
    with pytest.raises(ValidationError):
        ExportRequest(
            run_id="run-001",
            project_dir="runs/run-001/project",
            preset_name="Windows Desktop",
            target=ExportTarget.WINDOWS,
            output_path="runs/run-001/export/game.exe",
            extra="invalid",
        )
