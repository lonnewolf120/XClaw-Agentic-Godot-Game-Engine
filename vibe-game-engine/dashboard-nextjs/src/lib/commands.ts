import path from "path";

const projectRoot = path.resolve(process.cwd(), "..");
const pythonExec = process.env.PYTHON || "python";

export const COMMANDS: Record<string, { label: string; command: string[]; cwd: string }> = {
  run_tests: {
    label: "Run Pytest",
    command: [pythonExec, "-m", "pytest", "tests", "-q"],
    cwd: projectRoot,
  },
  run_smoke: {
    label: "Run Smoke Prompt",
    command: [pythonExec, "scripts/smoke_single_prompt.py"],
    cwd: projectRoot,
  },
  run_benchmark: {
    label: "Run Benchmark",
    command: [pythonExec, "scripts/qa_benchmark.py"],
    cwd: projectRoot,
  },
  run_asset_gate: {
    label: "Run Asset Quality Gate",
    command: [pythonExec, "scripts/run_asset_quality_gate.py"],
    cwd: projectRoot,
  },
  triage_escalations: {
    label: "Triage Escalations",
    command: [pythonExec, "scripts/triage_escalations.py"],
    cwd: projectRoot,
  },
};

export const PROJECT_ROOT = projectRoot;
