from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.template_catalog import load_template_catalog


POLICY_PATH = PROJECT_ROOT / "config" / "operational_policies.json"


def _read_policy(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _normalized_host(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def _is_allowed_source(url: str, allowed_domains: set[str]) -> bool:
    host = _normalized_host(url)
    return any(host == domain or host.endswith(f".{domain}") for domain in allowed_domains)


def _is_direct_download(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    return path.endswith((".zip", ".ogg", ".wav", ".png", ".jpg", ".jpeg", ".webm", ".glb", ".mp3", ".mp4"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync template assets from direct source URLs.")
    parser.add_argument(
        "--catalog",
        default=str(PROJECT_ROOT / "config" / "template_catalog.json"),
        help="Path to template catalog JSON.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned downloads without writing files.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate catalog direct links and domains without downloading.",
    )
    args = parser.parse_args()

    catalog = load_template_catalog(args.catalog)
    policy = _read_policy(POLICY_PATH)
    allowed_domains = {item.lower() for item in policy.get("asset_resolution", {}).get("allowed_online_sources", [])}

    downloaded = 0
    skipped = 0
    validated = 0
    invalid = 0

    for template in catalog.templates:
        for asset in template.assets:
            source_url = asset.source.download_url
            target_path = PROJECT_ROOT / asset.local_path

            if not _is_allowed_source(source_url, allowed_domains):
                invalid += 1
                skipped += 1
                print(f"skip_untrusted_domain asset_id={asset.asset_id} url={source_url}")
                continue

            if not _is_direct_download(source_url):
                invalid += 1
                skipped += 1
                print(f"skip_non_direct_url asset_id={asset.asset_id} url={source_url}")
                continue

            validated += 1

            if args.validate_only:
                print(f"validated asset_id={asset.asset_id} url={source_url}")
                continue

            if target_path.exists() and target_path.stat().st_size > 0:
                skipped += 1
                print(f"skip_existing asset_id={asset.asset_id} path={target_path}")
                continue

            if args.dry_run:
                downloaded += 1
                print(f"dry_run_download asset_id={asset.asset_id} -> {target_path}")
                continue

            target_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with urllib.request.urlopen(source_url, timeout=30) as response:
                    data = response.read()
                target_path.write_bytes(data)
                downloaded += 1
                print(f"downloaded asset_id={asset.asset_id} bytes={len(data)} path={target_path}")
            except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                skipped += 1
                print(f"download_failed asset_id={asset.asset_id} reason={exc}")

    print(
        json.dumps(
            {
                "validated": validated,
                "invalid": invalid,
                "downloaded": downloaded,
                "skipped": skipped,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
