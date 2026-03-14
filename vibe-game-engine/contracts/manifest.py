from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict, Field, StrictStr

from contracts.export import ExportResult
from contracts.godot_patch import GodotFilePatch
from contracts.project_spec import ProjectSpec
from contracts.run_state import RunMode
from contracts.validation import ValidationReport


class FinalManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    run_id: StrictStr
    prompt: StrictStr
    mode: RunMode
    created_at_utc: StrictStr

    project_spec: ProjectSpec
    files_changed: List[StrictStr] = Field(default_factory=list)
    applied_patches: List[GodotFilePatch] = Field(default_factory=list)

    validation_report: ValidationReport
    export_result: ExportResult

    validation_log_paths: List[StrictStr] = Field(default_factory=list)
    export_log_paths: List[StrictStr] = Field(default_factory=list)
    artifact_checksums: List[StrictStr] = Field(default_factory=list)
