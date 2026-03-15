from __future__ import annotations

import json
import os
import subprocess
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_ROOT = PROJECT_ROOT / "dashboard"
COMMAND_LOG_DIR = PROJECT_ROOT / "runs" / "dashboard_commands"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _python_exec() -> str:
    return os.environ.get("PYTHON", "python")


COMMANDS: dict[str, dict[str, Any]] = {
    "run_tests": {
        "label": "Run Pytest",
        "command": [_python_exec(), "-m", "pytest", "tests", "-q"],
        "cwd": str(PROJECT_ROOT),
    },
    "run_smoke": {
        "label": "Run Smoke Prompt",
        "command": [_python_exec(), "scripts/smoke_single_prompt.py"],
        "cwd": str(PROJECT_ROOT),
    },
    "run_benchmark": {
        "label": "Run Benchmark",
        "command": [_python_exec(), "scripts/qa_benchmark.py"],
        "cwd": str(PROJECT_ROOT),
    },
    "run_asset_gate": {
        "label": "Run Asset Quality Gate",
        "command": [_python_exec(), "scripts/run_asset_quality_gate.py"],
        "cwd": str(PROJECT_ROOT),
    },
    "triage_escalations": {
        "label": "Triage Escalations",
        "command": [_python_exec(), "scripts/triage_escalations.py"],
        "cwd": str(PROJECT_ROOT),
    },
}


@dataclass
class CommandJob:
    job_id: str
    command_id: str
    status: str
    started_at_utc: str
    ended_at_utc: str = ""
    return_code: int | None = None
    log_path: str = ""


JOBS_LOCK = threading.Lock()
JOBS: dict[str, CommandJob] = {}


def _read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _resolve_agent_states() -> list[dict[str, str]]:
    running_labels: set[str] = set()
    with JOBS_LOCK:
        for job in JOBS.values():
            if job.status == "running":
                running_labels.add(job.command_id)

    return [
        {"name": "Project Manager", "state": "active" if "run_benchmark" in running_labels else "idle"},
        {"name": "Coordinator", "state": "active" if "run_smoke" in running_labels else "idle"},
        {"name": "Coding Agent", "state": "active" if "run_smoke" in running_labels else "idle"},
        {"name": "Debugger Agent", "state": "active" if "run_smoke" in running_labels else "idle"},
        {"name": "Exporter Agent", "state": "idle"},
        {"name": "QA Agent", "state": "active" if "run_tests" in running_labels else "idle"},
    ]


def _recent_run_dirs(limit: int = 10) -> list[dict[str, str]]:
    runs_dir = PROJECT_ROOT / "runs"
    if not runs_dir.exists():
        return []

    entries = [p for p in runs_dir.glob("run-*") if p.is_dir()]
    entries.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    items: list[dict[str, str]] = []
    for path in entries[:limit]:
        ticket = path / ".vibe" / "escalation" / "needs_human_ticket.json"
        state = "needs_human" if ticket.exists() else "completed_or_unknown"
        items.append({"run_id": path.name, "state": state, "path": str(path)})
    return items


def build_overview() -> dict[str, Any]:
    benchmark_latest = _read_json(PROJECT_ROOT / "benchmarks" / "results" / "latest.json", {})
    benchmark_summary = benchmark_latest.get("summary", {}) if isinstance(benchmark_latest, dict) else {}
    queue_rows = _read_jsonl(PROJECT_ROOT / "runs" / "needs_human_queue.jsonl")
    triage_rows = _read_jsonl(PROJECT_ROOT / "runs" / "escalation_triage.jsonl")

    return {
        "timestamp_utc": _utc_now(),
        "kpis": {
            "benchmark_success_rate": benchmark_summary.get("success_rate", 0),
            "benchmark_total_prompts": benchmark_summary.get("total_prompts", 0),
            "needs_human_queue_items": len(queue_rows),
            "triage_batches": len(triage_rows),
        },
        "agents": _resolve_agent_states(),
        "recent_runs": _recent_run_dirs(),
        "latest_benchmark": benchmark_summary,
        "latest_triage": triage_rows[-1] if triage_rows else {},
        "commands": [{"id": key, "label": value["label"]} for key, value in COMMANDS.items()],
    }


def _run_job(job: CommandJob) -> None:
    config = COMMANDS[job.command_id]
    COMMAND_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = COMMAND_LOG_DIR / f"{job.job_id}.log"

    with JOBS_LOCK:
        job.log_path = str(log_path)
        JOBS[job.job_id] = job

    with log_path.open("w", encoding="utf-8") as handle:
        handle.write(f"[{_utc_now()}] START {job.command_id}\n")
        handle.write(" ".join(config["command"]) + "\n\n")
        handle.flush()
        proc = subprocess.run(
            config["command"],
            cwd=config["cwd"],
            stdout=handle,
            stderr=subprocess.STDOUT,
            check=False,
        )

    with JOBS_LOCK:
        job.status = "completed" if proc.returncode == 0 else "failed"
        job.return_code = int(proc.returncode)
        job.ended_at_utc = _utc_now()
        JOBS[job.job_id] = job


def _start_job(command_id: str) -> CommandJob:
    if command_id not in COMMANDS:
        raise ValueError("unsupported command_id")

    job = CommandJob(
        job_id=f"job-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
        command_id=command_id,
        status="running",
        started_at_utc=_utc_now(),
    )
    thread = threading.Thread(target=_run_job, args=(job,), daemon=True)
    thread.start()
    return job


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASHBOARD_ROOT), **kwargs)

    def _send_json(self, payload: Any, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/overview":
            self._send_json(build_overview())
            return
        if parsed.path == "/api/jobs":
            with JOBS_LOCK:
                jobs = [asdict(job) for job in JOBS.values()]
            jobs.sort(key=lambda item: item["started_at_utc"], reverse=True)
            self._send_json({"jobs": jobs})
            return
        if parsed.path == "/api/commands":
            self._send_json(
                {
                    "commands": [
                        {"id": key, "label": value["label"]}
                        for key, value in COMMANDS.items()
                    ]
                }
            )
            return
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/commands/run":
            self._send_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
        try:
            payload = json.loads(body)
            command_id = str(payload.get("command_id", ""))
            job = _start_job(command_id)
            self._send_json({"job": asdict(job)}, status=HTTPStatus.ACCEPTED)
        except (json.JSONDecodeError, ValueError):
            self._send_json({"error": "invalid_request"}, status=HTTPStatus.BAD_REQUEST)


def main() -> int:
    host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    port = int(os.environ.get("DASHBOARD_PORT", "8787"))
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    print(f"dashboard_server=http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())