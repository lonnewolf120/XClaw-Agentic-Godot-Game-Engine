from __future__ import annotations

from typing import Any, Dict


def model_copy_compat(model: Any, update: Dict[str, Any]) -> Any:
    if hasattr(model, "model_copy"):
        return model.model_copy(update=update)
    return model.copy(update=update)
