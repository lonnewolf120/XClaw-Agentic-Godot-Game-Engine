from __future__ import annotations

from pydantic import BaseModel

try:
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover - pydantic v1 fallback
    ConfigDict = None  # type: ignore[assignment]


if hasattr(BaseModel, "model_validate") and ConfigDict is not None:

    class StrictModel(BaseModel):
        model_config = ConfigDict(extra="forbid", strict=True)

else:

    class StrictModel(BaseModel):
        class Config:
            extra = "forbid"
