from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.asset_quality_gate import run_asset_quality_gate


def test_asset_quality_gate_passes_for_valid_assets(tmp_path) -> None:
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "asset_fallback_starter_library": {
                    "max_total_assets": 4,
                    "constraints": {
                        "max_texture_resolution": 1024,
                        "allowed_formats": ["png", "ogg", "wav"],
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    assets = tmp_path / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "hero_512x512.png").write_bytes(b"x")
    (assets / "ui_click.ogg").write_bytes(b"y")

    result = run_asset_quality_gate(assets, policy_path)
    assert result.success is True
    assert result.issues == []


def test_asset_quality_gate_detects_invalid_files(tmp_path) -> None:
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "asset_fallback_starter_library": {
                    "max_total_assets": 1,
                    "constraints": {
                        "max_texture_resolution": 1024,
                        "allowed_formats": ["png", "ogg", "wav"],
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    assets = tmp_path / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "hero_2048x2048.png").write_bytes(b"x")
    (assets / "readme.txt").write_text("bad", encoding="utf-8")

    result = run_asset_quality_gate(assets, policy_path)
    assert result.success is False
    assert any("asset_count_exceeded" in issue for issue in result.issues)
    assert any("texture_resolution_exceeded" in issue for issue in result.issues)
    assert any("disallowed_format" in issue for issue in result.issues)