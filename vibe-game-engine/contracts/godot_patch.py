from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import Field, StrictBool, StrictStr, conint

from contracts.base import StrictModel

PositiveStrictInt = conint(strict=True, ge=1)


class PatchOp(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class PatchHunk(StrictModel):

    start_line: PositiveStrictInt
    end_line: PositiveStrictInt
    replacement: StrictStr


class GodotFilePatch(StrictModel):

    patch_id: StrictStr
    op: PatchOp
    file_path: StrictStr
    language: StrictStr
    reason: StrictStr
    full_content: Optional[StrictStr] = None
    hunks: List[PatchHunk] = Field(default_factory=list)
    creates_backup: StrictBool = True


class PatchBatch(StrictModel):

    run_id: StrictStr
    attempt: PositiveStrictInt
    patches: List[GodotFilePatch] = Field(default_factory=list)
