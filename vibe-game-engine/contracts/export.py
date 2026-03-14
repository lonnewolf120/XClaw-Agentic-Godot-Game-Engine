from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import Field, StrictBool, StrictStr, conint

from contracts.base import StrictModel

NonNegativeStrictInt = conint(strict=True, ge=0)


class ExportTarget(str, Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    WEB = "web"


class ExportRequest(StrictModel):

    run_id: StrictStr
    project_dir: StrictStr
    preset_name: StrictStr
    target: ExportTarget
    output_path: StrictStr


class ExportArtifact(StrictModel):

    target: ExportTarget
    artifact_path: StrictStr
    size_bytes: NonNegativeStrictInt
    sha256: StrictStr


class ExportResult(StrictModel):

    run_id: StrictStr
    success: StrictBool
    command: StrictStr
    log_paths: List[StrictStr] = Field(default_factory=list)
    artifacts: List[ExportArtifact] = Field(default_factory=list)
    error_summary: StrictStr = ""
