from __future__ import annotations

import json
from pathlib import Path

from contracts.template_catalog import TemplateCatalog, TemplateDefinition


def load_template_catalog(catalog_path: str | Path) -> TemplateCatalog:
    payload = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    if hasattr(TemplateCatalog, "model_validate"):
        return TemplateCatalog.model_validate(payload)
    return TemplateCatalog.parse_obj(payload)


def _score_template(prompt: str, template: TemplateDefinition) -> int:
    lowered = prompt.lower()
    score = 0
    if template.dimension == "3d" and "3d" in lowered:
        score += 4
    if template.dimension == "2d" and "3d" not in lowered:
        score += 2

    for tag in template.tags:
        if tag.lower() in lowered:
            score += 3

    return score


def select_template_from_prompt(
    prompt: str,
    catalog_path: str | Path,
    workspace_root: str | Path,
) -> str:
    catalog = load_template_catalog(catalog_path)
    root = Path(workspace_root)

    candidates: list[tuple[int, TemplateDefinition]] = []
    for template in catalog.templates:
        template_root = root / template.path
        if not (template_root / "project.godot").exists():
            continue
        candidates.append((_score_template(prompt, template), template))

    if not candidates:
        fallback = root / catalog.default_template_path
        if fallback.exists():
            return catalog.default_template_path
        raise FileNotFoundError("No usable templates found in catalog")

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1].path
