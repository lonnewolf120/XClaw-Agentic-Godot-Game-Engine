#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <run_id> <project_dir> [attempt]"
  exit 2
fi

RUN_ID="$1"
PROJECT_DIR="$2"
ATTEMPT="${3:-1}"
GODOT_BIN="${GODOT_BIN:-godot4}"
TIMEOUT_CMD="${TIMEOUT_CMD:-timeout}"
MAX_SECONDS="${VALIDATION_TIMEOUT_SECONDS:-120}"

VALIDATION_DIR="${PROJECT_DIR}/.vibe/validation"
mkdir -p "${VALIDATION_DIR}"

IMPORT_LOG="${VALIDATION_DIR}/import_attempt_${ATTEMPT}.log"
CHECK_LOG="${VALIDATION_DIR}/check_attempt_${ATTEMPT}.log"
SMOKE_LOG="${VALIDATION_DIR}/smoke_attempt_${ATTEMPT}.log"
REPORT_JSON="${VALIDATION_DIR}/validation_report_attempt_${ATTEMPT}.json"

run_bounded() {
  local stage="$1"
  local log_file="$2"
  shift 2

  if ! "${TIMEOUT_CMD}" "${MAX_SECONDS}" "$@" >"${log_file}" 2>&1; then
    echo "${stage} command failed" >>"${log_file}"
  fi
}

run_bounded "import" "${IMPORT_LOG}" "${GODOT_BIN}" --headless --path "${PROJECT_DIR}" --quit
run_bounded "check" "${CHECK_LOG}" "${GODOT_BIN}" --headless --path "${PROJECT_DIR}" --check-only --quit
run_bounded "smoke" "${SMOKE_LOG}" "${GODOT_BIN}" --headless --path "${PROJECT_DIR}" --quit-after 1800

python -m tools.log_parser \
  --run-id "${RUN_ID}" \
  --attempt "${ATTEMPT}" \
  --logs "${IMPORT_LOG}" "${CHECK_LOG}" "${SMOKE_LOG}" \
  --output "${REPORT_JSON}"

python -m tools.log_parser --exit-code-from-report "${REPORT_JSON}"
