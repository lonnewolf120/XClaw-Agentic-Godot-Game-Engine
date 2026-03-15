from __future__ import annotations

from typing import Optional

from pydantic import StrictBool, StrictInt, StrictStr, conlist

from contracts.base import StrictModel


def _non_empty_conlist(item_type):
    try:
        return conlist(item_type, min_length=1)
    except TypeError:  # pragma: no cover - pydantic v1 fallback
        return conlist(item_type, min_items=1)


NonEmptyStrictStrList = _non_empty_conlist(StrictStr)


class AssetSource(StrictModel):
    provider: StrictStr
    author: StrictStr
    source_url: StrictStr
    download_url: StrictStr
    license: StrictStr
    attribution: StrictStr


class TemplateAsset(StrictModel):
    asset_id: StrictStr
    category: StrictStr
    local_path: StrictStr
    checksum_sha256: StrictStr
    compatible_genres: NonEmptyStrictStrList
    tags: NonEmptyStrictStrList
    source: AssetSource


class TemplateDefinition(StrictModel):
    template_id: StrictStr
    path: StrictStr
    dimension: StrictStr
    tags: NonEmptyStrictStrList
    credit_cost_hint: StrictInt
    description: Optional[StrictStr] = None
    editable: Optional[StrictBool] = None
    assets: list[TemplateAsset] = []


class TemplateCatalog(StrictModel):
    version: StrictStr
    default_template_path: StrictStr
    templates: _non_empty_conlist(TemplateDefinition)
