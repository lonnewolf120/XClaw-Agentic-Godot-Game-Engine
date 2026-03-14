from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr


class ExportTarget(str, Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    WEB = "web"


class ExportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    run_id: StrictStr
    project_dir: StrictStr
    preset_name: StrictStr
    target: ExportTarget
    output_path: StrictStr


class ExportArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    target: ExportTarget
    artifact_path: StrictStr
    size_bytes: StrictInt = Field(ge=0)
    sha256: StrictStr


class ExportResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    run_id: StrictStr
    success: StrictBool
    command: StrictStr
    log_paths: List[StrictStr] = Field(default_factory=list)
    artifacts: List[ExportArtifact] = Field(default_factory=list)
    error_summary: StrictStr = ""
