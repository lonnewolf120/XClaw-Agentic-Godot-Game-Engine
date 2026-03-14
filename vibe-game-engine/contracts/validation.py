from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr


class ValidationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


class ValidationStage(str, Enum):
    IMPORT = "import"
    CHECK = "check"
    SMOKE = "smoke"


class ValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    stage: ValidationStage
    severity: ValidationSeverity
    message: StrictStr
    file_path: Optional[StrictStr] = None
    line: Optional[StrictInt] = Field(default=None, ge=1)
    matched_pattern: Optional[StrictStr] = None


class ValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    run_id: StrictStr
    attempt: StrictInt = Field(ge=1)
    success: StrictBool
    timed_out: StrictBool = False
    stage_logs: List[StrictStr] = Field(default_factory=list)
    issues: List[ValidationIssue] = Field(default_factory=list)
    fatal_count: StrictInt = Field(default=0, ge=0)
    error_count: StrictInt = Field(default=0, ge=0)
    warning_count: StrictInt = Field(default=0, ge=0)
    summary: StrictStr
