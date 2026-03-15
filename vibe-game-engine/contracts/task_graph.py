from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import Field, StrictBool, StrictStr, conint, conlist

from contracts.base import StrictModel

PositiveStrictInt = conint(strict=True, ge=1)


def _non_empty_conlist(item_type):
    try:
        return conlist(item_type, min_length=1)
    except TypeError:  # pragma: no cover - pydantic v1 fallback
        return conlist(item_type, min_items=1)


NonEmptyStrictStrList = _non_empty_conlist(StrictStr)


class TaskType(str, Enum):
    CODE = "code"
    SCENE = "scene"
    ASSET = "asset"
    VALIDATION = "validation"
    EXPORT = "export"


class TaskPriority(str, Enum):
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


class TaskNode(StrictModel):
    task_id: StrictStr
    title: StrictStr
    task_type: TaskType
    priority: TaskPriority
    owner: StrictStr
    depends_on: list[StrictStr] = Field(default_factory=list)
    acceptance_criteria: NonEmptyStrictStrList
    estimated_minutes: PositiveStrictInt
    blocking: StrictBool = False
    notes: Optional[StrictStr] = None


class TaskGraph(StrictModel):
    run_id: StrictStr
    summary: StrictStr
    nodes: NonEmptyStrictStrList
    tasks: _non_empty_conlist(TaskNode)
