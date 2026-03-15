"""Project Manager agent stub for Milestone 3.

Responsible for ingesting prompt, validating ProjectSpec, and creating orchestration TaskGraph.
"""

from __future__ import annotations

from contracts.project_spec import (
    ComplexityTier,
    GameDimension,
    GameplayLoopSpec,
    PlatformTarget,
    ProjectSpec,
    ScopeGuardrails,
)
from contracts.run_state import RunMode
from contracts.task_graph import TaskGraph, TaskNode, TaskPriority, TaskType


def _infer_dimension(prompt: str) -> GameDimension:
    lowered = prompt.lower()
    if "3d" in lowered:
        return GameDimension.THREE_D
    return GameDimension.TWO_D


def _infer_mechanics(prompt: str) -> list[str]:
    lowered = prompt.lower()
    mechanics: list[str] = []
    if "jump" in lowered or "platform" in lowered:
        mechanics.append("jump")
    if "shoot" in lowered:
        mechanics.append("shoot")
    if "puzzle" in lowered:
        mechanics.append("solve")
    if not mechanics:
        mechanics.append("move")
    return mechanics


def build_project_spec(prompt: str) -> ProjectSpec:
    """Create a minimal project specification from a natural language prompt."""
    normalized_prompt = prompt.strip()
    if not normalized_prompt:
        raise ValueError("prompt must not be empty")

    return ProjectSpec(
        run_id="run-seeded",
        title="Vibe Generated Project",
        mode=RunMode.STANDALONE,
        game_dimension=_infer_dimension(normalized_prompt),
        complexity=ComplexityTier.SMALL,
        prompt_summary=normalized_prompt[:180],
        core_mechanics=_infer_mechanics(normalized_prompt),
        target_platforms=[PlatformTarget.WINDOWS],
        gameplay_loop=GameplayLoopSpec(
            objective="Complete the primary objective",
            win_condition="Reach level goal",
            fail_condition="Lose all health",
            estimated_session_minutes=10,
        ),
        scope_guardrails=ScopeGuardrails(
            max_levels=1,
            max_playable_characters=1,
            multiplayer_enabled=False,
        ),
        selected_template="templates/base_2d_platformer",
    )


def build_task_graph(spec: ProjectSpec) -> TaskGraph:
    """Generate a task graph from an approved ProjectSpec."""
    tasks = [
        TaskNode(
            task_id="T-INTAKE",
            title="Ingest prompt and scope",
            task_type=TaskType.CODE,
            priority=TaskPriority.P0,
            owner="project_manager",
            depends_on=[],
            acceptance_criteria=["ProjectSpec schema validates"],
            estimated_minutes=5,
            blocking=True,
        ),
        TaskNode(
            task_id="T-PLAN",
            title="Build deterministic task plan",
            task_type=TaskType.SCENE,
            priority=TaskPriority.P0,
            owner="coordinator",
            depends_on=["T-INTAKE"],
            acceptance_criteria=["TaskGraph schema validates"],
            estimated_minutes=5,
            blocking=True,
        ),
        TaskNode(
            task_id="T-VALIDATE",
            title="Run validation loop",
            task_type=TaskType.VALIDATION,
            priority=TaskPriority.P0,
            owner="debugger",
            depends_on=["T-PLAN"],
            acceptance_criteria=["Validation loop reaches terminal status"],
            estimated_minutes=10,
            blocking=True,
        ),
    ]

    return TaskGraph(
        run_id=spec.run_id,
        summary=f"Task graph for {spec.title}",
        nodes=["intake", "planning", "validation", "debug"],
        tasks=tasks,
    )
