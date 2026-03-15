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
    catalog_path: str | Path | None = None,
) -> AssetQualityResult:
    root = Path(assets_root)
    policy = _load_policy(policy_path)
    starter = policy["asset_fallback_starter_library"]
    constraints = starter["constraints"]
    allowed_domains = policy.get("asset_resolution", {}).get("allowed_online_sources", [])

    max_assets = int(starter["max_total_assets"])
    max_texture_resolution = int(constraints["max_texture_resolution"])
    allowed_formats = {f".{ext}" for ext in constraints["allowed_formats"]}

    issues: list[str] = []
    
    # Check domain allowlist in catalog if provided
    if catalog_path and Path(catalog_path).exists():
        from tools.template_catalog import load_template_catalog
        from urllib.parse import urlparse
        
        catalog = load_template_catalog(catalog_path)
        for template in catalog.templates:
            for asset in template.assets:
                for url in [asset.source.source_url, asset.source.download_url]:
                    if not url or url == "na":
                        continue
                    parsed_url = urlparse(url)
                    domain = parsed_url.netloc.lower()
                    if domain.startswith("www."):
                        domain = domain[4:]
                    # Check if domain matches any of the allowed online sources
                    is_allowed = False
                    for allowed in allowed_domains:
                        allowed_lower = allowed.lower()
                        if allowed_lower.startswith("www."):
                            allowed_lower = allowed_lower[4:]
                        if domain == allowed_lower or domain.endswith("." + allowed_lower):
                            is_allowed = True
                            break
                    if not is_allowed:
                        issues.append(f"disallowed_domain:{template.template_id}/{asset.asset_id}:{domain}")

    files = [p for p in root.rglob("*") if p.is_file()]
    checked_files = len(files)

    if checked_files > max_assets:
        issues.append(f"asset_count_exceeded: {checked_files}>{max_assets}")

    for file_path in files:
        if file_path.name == "manifest.json":
            continue

        suffix = file_path.suffix.lower()
        if suffix not in allowed_formats:
            issues.append(f"disallowed_format:{file_path.name}")

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