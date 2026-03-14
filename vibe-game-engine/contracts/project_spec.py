from __future__ import annotations

from enum import Enum

from pydantic import StrictBool, StrictStr, conint, conlist

from contracts.base import StrictModel
from contracts.run_state import RunMode

BoundedSessionMinutes = conint(strict=True, ge=1, le=30)
BoundedLevels = conint(strict=True, ge=1, le=10)
BoundedPlayableCharacters = conint(strict=True, ge=1, le=4)


def _non_empty_conlist(item_type):
    try:
        return conlist(item_type, min_length=1)
    except TypeError:  # pragma: no cover - pydantic v1 fallback
        return conlist(item_type, min_items=1)


NonEmptyStrictStrList = _non_empty_conlist(StrictStr)


class GameDimension(str, Enum):
    TWO_D = "2d"
    THREE_D = "3d"


class ComplexityTier(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"


class PlatformTarget(str, Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    WEB = "web"


NonEmptyPlatformList = _non_empty_conlist(PlatformTarget)


class GameplayLoopSpec(StrictModel):

    objective: StrictStr
    win_condition: StrictStr
    fail_condition: StrictStr
    estimated_session_minutes: BoundedSessionMinutes


class ScopeGuardrails(StrictModel):

    max_levels: BoundedLevels = 3
    max_playable_characters: BoundedPlayableCharacters = 2
    multiplayer_enabled: StrictBool = False


class ProjectSpec(StrictModel):

    run_id: StrictStr
    title: StrictStr
    mode: RunMode
    game_dimension: GameDimension
    complexity: ComplexityTier
    prompt_summary: StrictStr
    core_mechanics: NonEmptyStrictStrList
    target_platforms: NonEmptyPlatformList
    gameplay_loop: GameplayLoopSpec
    scope_guardrails: ScopeGuardrails
    selected_template: StrictStr
