from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr

from contracts.run_state import RunMode


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


class GameplayLoopSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    objective: StrictStr
    win_condition: StrictStr
    fail_condition: StrictStr
    estimated_session_minutes: StrictInt = Field(ge=1, le=30)


class ScopeGuardrails(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    max_levels: StrictInt = Field(default=3, ge=1, le=10)
    max_playable_characters: StrictInt = Field(default=2, ge=1, le=4)
    multiplayer_enabled: StrictBool = False


class ProjectSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    run_id: StrictStr
    title: StrictStr
    mode: RunMode
    game_dimension: GameDimension
    complexity: ComplexityTier
    prompt_summary: StrictStr
    core_mechanics: List[StrictStr] = Field(min_length=1)
    target_platforms: List[PlatformTarget] = Field(min_length=1)
    gameplay_loop: GameplayLoopSpec
    scope_guardrails: ScopeGuardrails
    selected_template: StrictStr
