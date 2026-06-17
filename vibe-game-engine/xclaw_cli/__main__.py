"""XClaw headless engine CLI.

    python -m xclaw_cli --prompt "Make the player jump much higher" \
        --template Starter-Kit-3D-Platformer --provider anthropic

    # With export:
    python -m xclaw_cli --prompt "Add double-jump" --export --export-target windows
"""
from __future__ import annotations

import argparse
import sys

from xclaw_cli.engine import generate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xclaw_cli", description="Headless LLM Godot game editor")
    parser.add_argument("--prompt", required=True, help="Natural-language change to make")
    parser.add_argument(
        "--template",
        default=None,
        help="Template folder under templates/ (omit to auto-select from the prompt)",
    )
    parser.add_argument(
        "--provider", default="anthropic",
        choices=["anthropic", "claude-code", "gemini", "ollama"],
        help="LLM provider (claude-code = local `claude` CLI, no API key)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name (provider default if omitted; anthropic defaults to claude-opus-4-8 — "
        "pass --model claude-haiku-4-5 for cheaper runs)",
    )
    parser.add_argument("--max-attempts", type=int, default=3, help="Self-correction retry cap")
    parser.add_argument(
        "--game", action="store_true",
        help="Schema-driven FULL-GAME authoring: emit a validated game_spec.json + player.gd and "
        "build a playable menu->levels->score->game-over game, gated by the automated playtest.",
    )
    parser.add_argument(
        "--export", action="store_true",
        help="Export a runnable artifact after a successful LLM loop",
    )
    parser.add_argument(
        "--export-target", default="windows", choices=["windows", "linux", "web"],
        help="Export platform (default: windows)",
    )
    parser.add_argument(
        "--export-path", default=None,
        help="Custom output path for the exported artifact",
    )
    args = parser.parse_args(argv)

    from xclaw_cli.llm import LLMError

    # ── Schema-driven full-game authoring path ─────────────────────────────
    if args.game:
        from xclaw_cli.game_engine import generate_game

        try:
            gres = generate_game(
                args.prompt,
                provider=args.provider,
                model=args.model,
                max_attempts=args.max_attempts,
                on_event=lambda m: print(f"[xclaw] {m}", flush=True),
            )
        except LLMError as exc:
            print(f"\nXCLAW_ERROR provider/model failure: {exc}", file=sys.stderr)
            return 2
        except FileNotFoundError as exc:
            print(f"\nXCLAW_ERROR {exc}", file=sys.stderr)
            return 2
        print(
            f"\nXCLAW_GAME_RESULT ok={gres.ok} run_id={gres.run_id} "
            f"attempts={gres.attempts} project={gres.project_dir}"
        )
        return 0 if gres.ok else 1

    try:
        result = generate(
            args.prompt,
            template=args.template,
            provider=args.provider,
            model=args.model,
            max_attempts=args.max_attempts,
            export=args.export,
            export_target=args.export_target,
            export_path=args.export_path,
            on_event=lambda m: print(f"[xclaw] {m}", flush=True),
        )
    except LLMError as exc:
        print(f"\nXCLAW_ERROR provider/model failure: {exc}", file=sys.stderr)
        tips = {
            "anthropic": "set ANTHROPIC_API_KEY (or run `ant auth login`); for cheaper runs pass --model claude-haiku-4-5.",
            "claude": "set ANTHROPIC_API_KEY (or run `ant auth login`); for cheaper runs pass --model claude-haiku-4-5.",
            "claude-code": "ensure the `claude` CLI is installed and logged in (claude /login), or set XCLAW_CLAUDE_EXE.",
            "gemini": "set a billing-enabled GEMINI_API_KEY, or try --model gemini-2.5-flash.",
            "ollama": "start Ollama (ollama serve) and pull the model, or switch --provider anthropic.",
        }
        print(f"  Tip: {tips.get(args.provider, 'check the provider credentials/quota, or switch --provider.')}",
              file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"\nXCLAW_ERROR {exc}", file=sys.stderr)
        return 2

    export_info = ""
    if result.export:
        if result.export.ok:
            mb = result.export.size_bytes / (1024 * 1024)
            export_info = f" export=OK ({mb:.1f}MB -> {result.export.output_path})"
        else:
            export_info = f" export=FAILED ({result.export.error})"

    print(
        f"\nXCLAW_RESULT ok={result.ok} run_id={result.run_id} "
        f"template={result.template} attempts={result.attempts} "
        f"project={result.project_dir}{export_info}"
    )
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
