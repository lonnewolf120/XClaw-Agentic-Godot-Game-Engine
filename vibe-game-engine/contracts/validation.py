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


class ValidationTier(str, Enum):
    STATIC_CHECK = "static_check"
    EDITOR_SAFE = "editor_safe"
    HEADLESS_SMOKE = "headless_smoke"
    EXPORT_PROBE = "export_probe"


class FailureClass(str, Enum):
    SCHEMA_INVALID = "schema_invalid"
    PATH_UNRESOLVED = "path_unresolved"
    NODE_MISSING = "node_missing"
    SIGNAL_TARGET_INVALID = "signal_target_invalid"
    SCRIPT_PARSE_ERROR = "script_parse_error"
    SCENE_IMPORT_ERROR = "scene_import_error"
    HEADLESS_BOOT_FAIL = "headless_boot_fail"
    EXPORT_FAIL = "export_fail"
    UNKNOWN = "unknown"


class ValidationIssue(StrictModel):

    tier: Optional[ValidationTier] = None
    stage: Optional[ValidationStage] = None
    severity: ValidationSeverity
    failure_class: Optional[FailureClass] = None
    message: StrictStr
    file_path: Optional[StrictStr] = None
    line: Optional[PositiveStrictInt] = None
    context_snippet: Optional[StrictStr] = None
    matched_pattern: Optional[StrictStr] = None


class ValidationReport(StrictModel):

    run_id: Optional[StrictStr] = None
    attempt: Optional[PositiveStrictInt] = None
    success: StrictBool
    timed_out: StrictBool = False
    completed_tiers: List[ValidationTier] = Field(default_factory=list)
    failed_tier: Optional[ValidationTier] = None
    stage_logs: List[StrictStr] = Field(default_factory=list)
    issues: List[ValidationIssue] = Field(default_factory=list)
    fatal_count: NonNegativeStrictInt = 0
    error_count: NonNegativeStrictInt = 0
    warning_count: NonNegativeStrictInt = 0
    summary: StrictStr
