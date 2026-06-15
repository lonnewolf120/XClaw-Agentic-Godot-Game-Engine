"""Godot project exporter.

Generates an export_presets.cfg for the target platform, invokes Godot's headless
export, and returns structured results including SHA-256 of the artifact. Self-contained
(no dependency on legacy contracts/ — same pattern as catalog.py).

Prerequisites for a successful export:
 - Godot export templates installed at %APPDATA%/Godot/export_templates/<version>/
   (download via Godot editor -> Editor -> Manage Export Templates, or from
   https://godotengine.org/download)
 - The project must already pass the headless gate (export won't fix script errors)
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable


class ExportTarget(str, Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    WEB = "web"


# Maps target → Godot platform string + recommended file extension.
_PLATFORM_MAP = {
    ExportTarget.WINDOWS: ("Windows Desktop", ".exe"),
    ExportTarget.LINUX: ("Linux", ".x86_64"),
    ExportTarget.WEB: ("Web", ".html"),
}


@dataclass
class ExportConfig:
    target: ExportTarget = ExportTarget.WINDOWS
    output_path: str | None = None  # resolved later if None
    embed_pck: bool = True


@dataclass
class ExportOutcome:
    ok: bool
    output_path: str = ""
    size_bytes: int = 0
    sha256: str = ""
    error: str = ""
    log: str = ""
    command: str = ""

    def summary(self) -> str:
        if self.ok:
            mb = self.size_bytes / (1024 * 1024)
            return f"exported {mb:.1f} MB -> {self.output_path}"
        return f"export_failed: {self.error}"


# ---------------------------------------------------------------------------
# Export-template detection
# ---------------------------------------------------------------------------

def _godot_version_from_exe(godot_exe: str) -> str | None:
    """Run `godot --version` and return the version tag (e.g. '4.6.1.stable')."""
    try:
        proc = subprocess.run(
            [godot_exe, "--headless", "--version"],
            capture_output=True, text=True, timeout=15, check=False,
        )
        line = (proc.stdout or "").strip().split("\n")[0].strip()
        # "4.6.1.stable.official.14d19694e" → "4.6.1.stable"
        parts = line.split(".")
        if len(parts) >= 3:
            # keep up to the label (stable/beta/rc)
            tag = ".".join(parts[:3])
            if len(parts) > 3 and not parts[3][0].isdigit():
                tag += f".{parts[3]}"
            return tag
    except Exception:
        pass
    return None


def find_export_templates(godot_exe: str) -> tuple[Path | None, str]:
    """Locate installed export templates; return (dir_or_None, version_tag)."""
    ver = _godot_version_from_exe(godot_exe)
    if not ver:
        return None, ""
    appdata = os.environ.get("APPDATA", "")
    if not appdata:
        return None, ver
    tpl_dir = Path(appdata) / "Godot" / "export_templates" / ver
    if tpl_dir.is_dir() and any(tpl_dir.iterdir()):
        return tpl_dir, ver
    return None, ver


# ---------------------------------------------------------------------------
# Preset generation
# ---------------------------------------------------------------------------

_WIN_PRESET_TEMPLATE = """\
[preset.0]

name="Windows Desktop"
platform="Windows Desktop"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="{export_path}"
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false

[preset.0.options]

custom_template/debug=""
custom_template/release=""
debug/export_console_wrapper=1
binary_format/embed_pck={embed_pck}
texture_format/s3tc_bptc=true
texture_format/etc2_astc=false
codesign/enable=false
application/modify_resources=true
application/icon=""
application/console_wrapper_icon=""
application/icon_interpolation=4
application/file_version=""
application/product_version=""
application/company_name=""
application/product_name=""
application/file_description=""
application/copyright=""
application/trademarks=""
application/export_angle=0
ssh_remote_deploy/enabled=false
"""

_LINUX_PRESET_TEMPLATE = """\
[preset.0]

name="Linux"
platform="Linux"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="{export_path}"
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false

[preset.0.options]

custom_template/debug=""
custom_template/release=""
debug/export_console_wrapper=1
binary_format/embed_pck={embed_pck}
texture_format/s3tc_bptc=true
texture_format/etc2_astc=false
ssh_remote_deploy/enabled=false
"""

_WEB_PRESET_TEMPLATE = """\
[preset.0]

name="Web"
platform="Web"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="{export_path}"
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false

[preset.0.options]

custom_template/debug=""
custom_template/release=""
variant/extensions_support=false
vram_texture_compression/for_desktop=true
vram_texture_compression/for_mobile=false
html/export_icon=true
html/custom_html_shell=""
html/head_include=""
html/canvas_resize_policy=2
html/focus_canvas_on_start=true
html/experimental_virtual_keyboard=false
progressive_web_app/enabled=false
"""

_PRESET_TEMPLATES = {
    ExportTarget.WINDOWS: _WIN_PRESET_TEMPLATE,
    ExportTarget.LINUX: _LINUX_PRESET_TEMPLATE,
    ExportTarget.WEB: _WEB_PRESET_TEMPLATE,
}


def write_export_preset(project_dir: Path, cfg: ExportConfig, rel_output: str) -> Path:
    """Write export_presets.cfg to the project; return the path."""
    template = _PRESET_TEMPLATES[cfg.target]
    embed = "true" if cfg.embed_pck else "false"
    content = template.format(export_path=rel_output, embed_pck=embed)
    preset_path = project_dir / "export_presets.cfg"
    preset_path.write_text(content, encoding="utf-8")
    return preset_path


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def export_project(
    project_dir: str | Path,
    godot_exe: str,
    cfg: ExportConfig | None = None,
    on_event: Callable[[str], None] | None = None,
) -> ExportOutcome:
    """Export the Godot project to a runnable artifact.

    Steps:
        1. Resolve the output path
        2. Check export templates
        3. Write export_presets.cfg
        4. Run godot --headless --export-release
        5. Verify the artifact
    """
    cfg = cfg or ExportConfig()
    project_dir = Path(project_dir).resolve()

    def emit(msg: str) -> None:
        if on_event:
            on_event(msg)

    platform_name, default_ext = _PLATFORM_MAP[cfg.target]

    # 1. Output path
    if cfg.output_path:
        output = Path(cfg.output_path).resolve()
    else:
        output = project_dir.parent / "export" / f"game{default_ext}"
    output.parent.mkdir(parents=True, exist_ok=True)
    emit(f"export: target={cfg.target.value} output={output}")

    # 2. Check export templates
    tpl_dir, ver = find_export_templates(godot_exe)
    if not tpl_dir:
        hint = (
            f"Godot export templates not installed for version {ver or '(unknown)'}.\n"
            f"Install via: Godot Editor -> Editor -> Manage Export Templates -> Download,\n"
            f"or from https://godotengine.org/download (Export Templates .tpz file)."
        )
        emit(f"export: FAILED — {hint}")
        return ExportOutcome(ok=False, error=f"export_templates_missing (v{ver})", log=hint)
    emit(f"export: templates found at {tpl_dir}")

    # 3. Write export_presets.cfg
    rel_output = f"export/game{default_ext}"  # relative path for the preset
    preset_path = write_export_preset(project_dir, cfg, rel_output)
    emit(f"export: wrote {preset_path}")

    # 4. Run export
    args = [
        godot_exe, "--headless",
        "--path", str(project_dir),
        "--export-release", platform_name,
        str(output),
    ]
    command = " ".join(args)
    emit(f"export: running {command}")

    log_path = project_dir.parent / "export" / "export.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            args, capture_output=True, text=True, timeout=300, check=False,
        )
        log_text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    except subprocess.TimeoutExpired as exc:
        log_text = f"TIMEOUT after 300s\n{exc.stdout or ''}"
        log_path.write_text(log_text, encoding="utf-8")
        return ExportOutcome(ok=False, error="export_timeout", log=log_text, command=command)
    except FileNotFoundError:
        return ExportOutcome(ok=False, error=f"godot_not_found: {godot_exe}", command=command)

    log_path.write_text(log_text, encoding="utf-8")

    # 5. Verify
    if not output.exists():
        error = f"export_no_artifact (exit={proc.returncode})"
        emit(f"export: FAILED — {error}")
        return ExportOutcome(ok=False, error=error, log=log_text, command=command)

    size = output.stat().st_size
    checksum = _sha256(output)
    emit(f"export: SUCCESS {size / (1024*1024):.1f} MB sha256={checksum[:16]}...")

    return ExportOutcome(
        ok=True,
        output_path=str(output),
        size_bytes=size,
        sha256=checksum,
        log=log_text,
        command=command,
    )
