from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import Field, StrictStr, conint

from contracts.base import StrictModel
from contracts.export import ExportResult
from contracts.godot_patch import PatchBatch
from contracts.validation import ValidationReport

PositiveStrictInt = conint(strict=True, ge=1)
NonNegativeStrictInt = conint(strict=True, ge=0)
RetryCapStrictInt = conint(strict=True, ge=1, le=3)


class RunMode(str, Enum):
    STANDALONE = "standalone"
    LIVE_BRIDGE = "live_bridge"
    PROJECT_ONLY = "project_only"


class RunStatus(str, Enum):
    INTAKE = "intake"
    PLANNING = "planning"
    VALIDATING = "validating"
    DEBUGGING = "debugging"
    COMPLETED = "completed"
    NEEDS_HUMAN = "needs_human"
    FAILED = "failed"


class OrchestrationNode(str, Enum):
    INTAKE = "intake"
    PLANNING = "planning"
    VALIDATION = "validation"
    DEBUG = "debug"
    DONE = "done"


class RetryEvent(StrictModel):

    attempt: PositiveStrictInt
    node: OrchestrationNode
    reason: StrictStr
    timestamp_utc: StrictStr


class ArtifactLogBundle(StrictModel):

    artifact_paths: List[StrictStr] = Field(default_factory=list)
    log_paths: List[StrictStr] = Field(default_factory=list)


class RunState(StrictModel):

    run_id: StrictStr
    prompt: StrictStr
    mode: RunMode = RunMode.STANDALONE
    status: RunStatus = RunStatus.INTAKE
    current_node: OrchestrationNode = OrchestrationNode.INTAKE

    retry_count: NonNegativeStrictInt = 0
    max_retries: RetryCapStrictInt = 3
    retry_events: List[RetryEvent] = Field(default_factory=list)

    workspace_dir: StrictStr
    artifacts: ArtifactLogBundle = Field(default_factory=ArtifactLogBundle)

    validation_report: Optional[ValidationReport] = None
    export_result: Optional[ExportResult] = None
    proposed_patch_batch: Optional[PatchBatch] = None

    failure_reason: Optional[StrictStr] = None
