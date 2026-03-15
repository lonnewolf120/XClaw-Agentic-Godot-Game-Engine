from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.sync_template_assets import _is_allowed_source, _is_direct_download


def test_is_direct_download_supports_querystring_assets() -> None:
    assert _is_direct_download("https://cdn.pixabay.com/audio/file.mp3?filename=test.mp3") is True
    assert _is_direct_download("https://kenney.nl/assets/ui-pack") is False


def test_is_allowed_source_matches_subdomains() -> None:
    allowed = {"pixabay.com", "kenney.nl"}
    assert _is_allowed_source("https://cdn.pixabay.com/video/clip.mp4", allowed) is True
    assert _is_allowed_source("https://files.kenney.nl/assets/ui-pack.zip", allowed) is True
    assert _is_allowed_source("https://example.com/file.zip", allowed) is False
