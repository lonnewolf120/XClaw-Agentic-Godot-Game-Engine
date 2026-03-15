from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_APP = REPO_ROOT / "vibe-game-engine" / "dashboard-nextjs"


def main() -> int:
    if not DASHBOARD_APP.exists():
        print("dashboard_nextjs_missing")
        return 1

    print(f"Starting Next.js dashboard from: {DASHBOARD_APP}")
    print("URL: http://127.0.0.1:3000")
    print("Press Ctrl+C to stop.")

    # This wrapper preserves the old command path while launching the new Next.js app.
    return subprocess.call(["npm", "run", "dev"], cwd=str(DASHBOARD_APP))


if __name__ == "__main__":
    raise SystemExit(main())
