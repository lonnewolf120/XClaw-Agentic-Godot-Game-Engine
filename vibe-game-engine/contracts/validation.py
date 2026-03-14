from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import Field, StrictBool, StrictStr, conint

from contracts.base import StrictModel

PositiveStrictInt = conint(strict=True, ge=1)
NonNegativeStrictInt = conint(strict=True, ge=0)


class ValidationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


class ValidationStage(str, Enum):
    IMPORT = "import"
    CHECK = "check"
    SMOKE = "smoke"


class ValidationIssue(StrictModel):

    stage: ValidationStage
    severity: ValidationSeverity
    message: StrictStr
    file_path: Optional[StrictStr] = None
    line: Optional[PositiveStrictInt] = None
    matched_pattern: Optional[StrictStr] = None


class ValidationReport(StrictModel):

    run_id: StrictStr
    attempt: PositiveStrictInt
    success: StrictBool
    timed_out: StrictBool = False
    stage_logs: List[StrictStr] = Field(default_factory=list)
    issues: List[ValidationIssue] = Field(default_factory=list)
    fatal_count: NonNegativeStrictInt = 0
    error_count: NonNegativeStrictInt = 0
    warning_count: NonNegativeStrictInt = 0
    summary: StrictStr
