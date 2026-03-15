from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AssetQualityResult:
    success: bool
    checked_files: int
    issues: list[str]


def _load_policy(policy_path: str | Path) -> dict:
    return json.loads(Path(policy_path).read_text(encoding="utf-8"))


def run_asset_quality_gate(
    assets_root: str | Path,
    policy_path: str | Path,
) -> AssetQualityResult:
    root = Path(assets_root)
    policy = _load_policy(policy_path)
    starter = policy["asset_fallback_starter_library"]
    constraints = starter["constraints"]

    max_assets = int(starter["max_total_assets"])
    max_texture_resolution = int(constraints["max_texture_resolution"])
    allowed_formats = {f".{ext}" for ext in constraints["allowed_formats"]}

    issues: list[str] = []
    files = [p for p in root.rglob("*") if p.is_file()]
    checked_files = len(files)

    if checked_files > max_assets:
        issues.append(f"asset_count_exceeded: {checked_files}>{max_assets}")

    for file_path in files:
        suffix = file_path.suffix.lower()
        if suffix not in allowed_formats:
            issues.append(f"disallowed_format:{file_path.name}")

        # Texture dimension check uses filename convention only in this deterministic gate:
        # hero_512x512.png is accepted, hero_2048x2048.png is rejected.
        stem = file_path.stem.lower()
        if "x" in stem and suffix == ".png":
            parts = stem.split("_")[-1]
            if "x" in parts:
                width_str, height_str = parts.split("x", 1)
                if width_str.isdigit() and height_str.isdigit():
                    width = int(width_str)
                    height = int(height_str)
                    if width > max_texture_resolution or height > max_texture_resolution:
                        issues.append(
                            f"texture_resolution_exceeded:{file_path.name}:{width}x{height}>{max_texture_resolution}"
                        )

    return AssetQualityResult(
        success=not issues,
        checked_files=checked_files,
        issues=issues,
    )