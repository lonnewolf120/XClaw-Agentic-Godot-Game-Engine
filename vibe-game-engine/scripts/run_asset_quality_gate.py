from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.asset_quality_gate import run_asset_quality_gate


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    assets_root = PROJECT_ROOT / "templates" / "base_2d_platformer" / "assets"
    assets_root.mkdir(parents=True, exist_ok=True)
    policy_path = PROJECT_ROOT / "config" / "operational_policies.json"
    result = run_asset_quality_gate(assets_root=assets_root, policy_path=policy_path)

    payload = {
        "success": result.success,
        "checked_files": result.checked_files,
        "issues": result.issues,
    }
    print(json.dumps(payload, indent=2))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())