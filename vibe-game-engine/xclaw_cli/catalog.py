"""Prompt -> template selection over the catalog data.

Self-contained on purpose. We read `config/template_catalog.json` for the tags /
descriptions, but do our OWN filtering and scoring and return a *folder name* that
`workspace.prepare_workspace` consumes directly.

This deliberately deviates from reusing `tools/template_catalog.select_template_from_prompt`,
which returns `../templates/X` path strings (two different path styles in one catalog) that
our single `TEMPLATES_DIR` can't cleanly validate or feed to `prepare_workspace`. The scoring
logic is trivial, so reimplementing it here is less friction than wrapping + post-processing
the legacy function. See XCLAW_HEADLESS_ENGINE_PLAN.md progress log (Phase 4).

Candidate set = every catalog entry whose basename has a valid `project.godot` under
`TEMPLATES_DIR`. Phase 4 proved (headless gate) that the non-Kenney 2D scaffolds
(base_2d_platformer / topdown_shooter / endless_runner) parse clean too, so they are
legitimate candidates — without them a "2D platformer" prompt would have no valid target.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from xclaw_cli import config

DEFAULT_TEMPLATE = "Starter-Kit-3D-Platformer"

_WORD = re.compile(r"[a-z0-9]+")
# Light stopword set so description overlap doesn't fire on filler words.
_STOP = {
    "with", "and", "the", "for", "game", "make", "create", "build", "your", "that",
    "this", "from", "into", "have", "kit", "starter", "basic", "simple", "small",
}


def _tokens(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if len(w) >= 3}


def _squash(text: str) -> str:
    """Collapse to alphanumerics so 'top-down'/'topdown' and 'first person'/'firstperson' match."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


@dataclass
class TemplateInfo:
    name: str          # folder under TEMPLATES_DIR (also what prepare_workspace wants)
    dimension: str     # "2d" | "3d" | ""
    tags: list[str]    # lowercased
    description: str    # lowercased ("" for the non-Kenney scaffolds)
    kenney: bool       # editable Kenney kit: human-made, preferred on ties


@dataclass
class Selection:
    name: str
    score: float
    reason: str


def _catalog_path() -> Path:
    return config.VIBE_DIR / "config" / "template_catalog.json"


def load_templates(catalog_path: str | Path | None = None) -> list[TemplateInfo]:
    """Load catalog entries that map (by basename) to a valid template under TEMPLATES_DIR."""
    path = Path(catalog_path) if catalog_path else _catalog_path()
    data = json.loads(path.read_text(encoding="utf-8"))
    out: list[TemplateInfo] = []
    for entry in data.get("templates", []):
        name = Path(entry.get("path", "")).name
        if not name:
            continue
        if not (config.TEMPLATES_DIR / name / "project.godot").exists():
            continue
        out.append(
            TemplateInfo(
                name=name,
                dimension=(entry.get("dimension") or "").strip().lower(),
                tags=[str(t).strip().lower() for t in entry.get("tags", []) if str(t).strip()],
                description=(entry.get("description") or "").strip().lower(),
                kenney=bool(entry.get("editable")),
            )
        )
    return out


def score_template(prompt: str, t: TemplateInfo) -> tuple[float, list[str]]:
    """Score one template against the prompt. Returns (score, human-readable reasons)."""
    p = prompt.lower()
    p_squashed = _squash(prompt)
    ptoks = _tokens(prompt)
    score = 0.0
    reasons: list[str] = []

    # --- Dimension: only when the prompt is explicit. Penalize the wrong dimension so a
    #     "2D ..." prompt never silently lands on a 3D kit (all Kenney kits are 3D).
    if "3d" in p:
        if t.dimension == "3d":
            score += 4; reasons.append("dim:3d")
        elif t.dimension == "2d":
            score -= 3; reasons.append("dim:-2d")
    elif "2d" in p:
        if t.dimension == "2d":
            score += 4; reasons.append("dim:2d")
        elif t.dimension == "3d":
            score -= 3; reasons.append("dim:-3d")

    # --- Tags (the genre signal). Skip bare dimension tags so "3d" can't double-count
    #     with the dimension score above (that bug would let micro_fps_3d beat Kenney FPS).
    for tag in t.tags:
        if tag in ("2d", "3d"):
            continue
        tag_sq = _squash(tag)
        # Longer tags: squashed-substring (handles 'top-down'~'topdown', plurals like
        # 'bullet'~'bullets', multi-word 'first person shooter'). Short tags: exact token
        # only, so a 3-letter tag like 'car' can't false-match inside 'scary'.
        matched = (tag_sq in p_squashed) if len(tag_sq) >= 4 else (tag in ptoks)
        if matched:
            score += 3; reasons.append(f"tag:{tag}")

    # --- Description overlap (lighter, capped). Only Kenney kits carry descriptions, which
    #     is a mild, intentional nudge toward the richer human-made templates.
    if t.description:
        overlap = (ptoks & _tokens(t.description)) - _STOP
        if overlap:
            bump = min(len(overlap), 2)
            score += bump
            reasons.append("desc:" + ",".join(sorted(overlap)[:3]))

    return score, reasons


def select_template(
    prompt: str, templates: list[TemplateInfo] | None = None
) -> Selection:
    """Pick the best template folder for a prompt. Falls back to DEFAULT_TEMPLATE on no signal.

    Tie-break order: higher score, then Kenney (human-made) kits first.
    """
    templates = templates if templates is not None else load_templates()
    if not templates:
        return Selection(DEFAULT_TEMPLATE, 0.0, "no catalog templates -> default")

    scored = []
    for t in templates:
        s, reasons = score_template(prompt, t)
        scored.append((s, t.kenney, t, reasons))
    # Sort by score, then prefer Kenney on ties.
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)

    best_score, _, best, best_reasons = scored[0]
    if best_score <= 0:
        return Selection(DEFAULT_TEMPLATE, best_score, "no strong signal -> default")

    return Selection(best.name, best_score, "; ".join(best_reasons) or "scored")
