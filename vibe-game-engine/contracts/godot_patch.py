from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr


class PatchOp(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class PatchHunk(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    start_line: StrictInt = Field(ge=1)
    end_line: StrictInt = Field(ge=1)
    replacement: StrictStr


class GodotFilePatch(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    patch_id: StrictStr
    op: PatchOp
    file_path: StrictStr
    language: StrictStr
    reason: StrictStr
    full_content: Optional[StrictStr] = None
    hunks: List[PatchHunk] = Field(default_factory=list)
    creates_backup: StrictBool = True


class PatchBatch(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    run_id: StrictStr
    attempt: StrictInt = Field(ge=1)
    patches: List[GodotFilePatch] = Field(default_factory=list)
