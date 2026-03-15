from __future__ import annotations

from pydantic import StrictInt, StrictStr, conlist

from contracts.base import StrictModel


def _non_empty_conlist(item_type):
    try:
        return conlist(item_type, min_length=1)
    except TypeError:  # pragma: no cover - pydantic v1 fallback
        return conlist(item_type, min_items=1)


NonEmptyStrictStrList = _non_empty_conlist(StrictStr)


class AssetSource(StrictModel):
    provider: StrictStr
    source_url: StrictStr
    license: StrictStr
    attribution: StrictStr


class TemplateAsset(StrictModel):
    asset_id: StrictStr
    category: StrictStr
    local_path: StrictStr
    tags: NonEmptyStrictStrList
    source: AssetSource


class TemplateDefinition(StrictModel):
    template_id: StrictStr
    path: StrictStr
    dimension: StrictStr
    tags: NonEmptyStrictStrList
    credit_cost_hint: StrictInt
    assets: list[TemplateAsset] = []


class TemplateCatalog(StrictModel):
    version: StrictStr
    default_template_path: StrictStr
    templates: _non_empty_conlist(TemplateDefinition)
