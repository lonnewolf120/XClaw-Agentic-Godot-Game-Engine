from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

from contracts.export import ExportResult
from contracts.validation import ValidationReport


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


class RetryEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    attempt: StrictInt = Field(ge=1)
    node: OrchestrationNode
    reason: StrictStr
    timestamp_utc: StrictStr


class ArtifactLogBundle(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    artifact_paths: List[StrictStr] = Field(default_factory=list)
    log_paths: List[StrictStr] = Field(default_factory=list)


class RunState(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    run_id: StrictStr
    prompt: StrictStr
    mode: RunMode = RunMode.STANDALONE
    status: RunStatus = RunStatus.INTAKE
    current_node: OrchestrationNode = OrchestrationNode.INTAKE

    retry_count: StrictInt = Field(default=0, ge=0)
    max_retries: StrictInt = Field(default=3, ge=1, le=3)
    retry_events: List[RetryEvent] = Field(default_factory=list)

    workspace_dir: StrictStr
    artifacts: ArtifactLogBundle = Field(default_factory=ArtifactLogBundle)

    validation_report: Optional[ValidationReport] = None
    export_result: Optional[ExportResult] = None

    failure_reason: Optional[StrictStr] = None
