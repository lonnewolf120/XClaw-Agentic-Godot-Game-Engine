from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.asset_resolver import resolve_assets_for_prompt
from tools.template_catalog import load_template_catalog, select_template_from_prompt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = PROJECT_ROOT / "config" / "template_catalog.json"
POLICY_PATH = PROJECT_ROOT / "config" / "operational_policies.json"


def test_template_catalog_loads() -> None:
    catalog = load_template_catalog(CATALOG_PATH)
    assert catalog.version == "v1"
    assert len(catalog.templates) >= 4


def test_template_selector_picks_3d_template() -> None:
    selected = select_template_from_prompt(
        prompt="Build a 3D fps arena with fast movement",
        catalog_path=CATALOG_PATH,
        workspace_root=PROJECT_ROOT,
    )
    assert selected == "templates/micro_fps_3d"


def test_template_selector_picks_kenney_racing_template() -> None:
    selected = select_template_from_prompt(
        prompt="Create an arcade racing game with vehicle drift and track laps",
        catalog_path=CATALOG_PATH,
        workspace_root=PROJECT_ROOT,
    )
    assert selected == "../templates/Starter-Kit-Racing"


def test_template_selector_picks_kenney_city_builder_template() -> None:
    selected = select_template_from_prompt(
        prompt="Build a 3d city builder with placement and removal of structures",
        catalog_path=CATALOG_PATH,
        workspace_root=PROJECT_ROOT,
    )
    assert selected == "../templates/Starter-Kit-City-Builder"


def test_asset_resolver_prefers_local_assets_before_generation() -> None:
    plan = resolve_assets_for_prompt(
        prompt="Create a tiny 2D platformer with jump",
        template_path="templates/base_2d_platformer",
        catalog_path=CATALOG_PATH,
        policy_path=POLICY_PATH,
        workspace_root=PROJECT_ROOT,
    )

    assert "templates/base_2d_platformer/assets/ui/button_set.png" in plan.selected_local_assets
    assert any(item == "generate:sprites" for item in plan.generated_asset_requests)
    assert len(plan.generated_asset_requests) <= 3
