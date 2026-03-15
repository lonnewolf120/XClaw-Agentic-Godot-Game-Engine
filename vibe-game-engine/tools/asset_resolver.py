from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from tools.template_catalog import load_template_catalog


@dataclass
class ResolvedAssetPlan:
    template_path: str
    mode: str
    selected_local_assets: list[str]
    generated_asset_requests: list[str]
    missing_categories: list[str]
    estimated_cost: int = 0


def _read_policy(policy_path: str | Path) -> dict:
    return json.loads(Path(policy_path).read_text(encoding="utf-8"))


def _required_categories(prompt: str) -> list[str]:
    lowered = prompt.lower()
    required = ["ui", "sfx", "music"]

    if "3d" in lowered:
        required.extend(["models", "textures"])
    else:
        required.extend(["sprites", "tiles"])

    if "cutscene" in lowered or "cinematic" in lowered:
        required.append("cutscenes")

    # Keep order stable while removing duplicates.
    deduped: list[str] = []
    for item in required:
        if item not in deduped:
            deduped.append(item)
    return deduped


def resolve_assets_for_prompt(
    prompt: str,
    *,
    template_path: str,
    catalog_path: str | Path,
    policy_path: str | Path,
    workspace_root: str | Path,
) -> ResolvedAssetPlan:
    catalog = load_template_catalog(catalog_path)
    policy = _read_policy(policy_path)
    root = Path(workspace_root)

    mode = str(policy.get("asset_resolution", {}).get("mode", "local_first"))

    template = None
    for item in catalog.templates:
        if item.path == template_path:
            template = item
            break
    if template is None:
        raise ValueError(f"Template missing from catalog: {template_path}")

    required = _required_categories(prompt)
    selected_local_assets: list[str] = []
    generated_asset_requests: list[str] = []
    missing_categories: list[str] = []

    for category in required:
        local_assets = [
            asset.local_path
            for asset in template.assets
            if asset.category == category and (root / asset.local_path).exists()
        ]

        if local_assets:
            selected_local_assets.extend(local_assets)
            continue

        if mode in {"local_first", "generate_first"}:
            generated_asset_requests.append(f"generate:{category}")
            continue

        missing_categories.append(category)

    gen_cost = int(policy.get("asset_resolution", {}).get("generation_cost_per_asset", 40))
    estimated_cost = len(generated_asset_requests) * gen_cost

    return ResolvedAssetPlan(
        template_path=template_path,
        mode=mode,
        selected_local_assets=selected_local_assets,
        generated_asset_requests=generated_asset_requests,
        missing_categories=missing_categories,
        estimated_cost=estimated_cost,
    )
