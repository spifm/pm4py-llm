#!/usr/bin/env bash
#
# Run the cleanup command in both the app and orchestrator containers,
# removing output/pipeline-results directories older than CLEANUP_RETENTION_MONTHS.
#
# The cutoff date (today minus CLEANUP_RETENTION_MONTHS months) is calculated
# inside the app container using Python, so it works on any host (macOS/Linux).
#
# CLEANUP_RETENTION_MONTHS is read from the .env file in the project root.
#
# By default runs in dry-run mode: shows what would be deleted without removing
# anything. Pass --apply to actually delete.
#
# Usage:
#   ./cleanup.sh              # dry-run (preview only)
#   ./cleanup.sh --apply      # actually delete
#
set -euo pipefail

cd "$(dirname "$0")"

# ---------- Parse flags ----------
APPLY=false
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=true ;;
    *) echo "Unknown argument: $arg" >&2; exit 1 ;;
  esac
done

# ---------- Load .env ----------
if [[ ! -f .env ]]; then
  echo "Error: .env file not found in $(pwd)" >&2
  exit 1
fi

# Export only CLEANUP_RETENTION_MONTHS from the .env file (ignore comments/blanks)
CLEANUP_RETENTION_MONTHS=""
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ "$line" =~ ^[[:space:]]*# ]] && continue
  [[ -z "${line// }" ]] && continue
  if [[ "$line" == CLEANUP_RETENTION_MONTHS=* ]]; then
    CLEANUP_RETENTION_MONTHS="${line#CLEANUP_RETENTION_MONTHS=}"
    break
  fi
done < .env

if [[ -z "$CLEANUP_RETENTION_MONTHS" ]]; then
  echo "Error: CLEANUP_RETENTION_MONTHS is not set in .env" >&2
  exit 1
fi

if ! [[ "$CLEANUP_RETENTION_MONTHS" =~ ^[1-9][0-9]*$ ]]; then
  echo "Error: CLEANUP_RETENTION_MONTHS must be a positive integer, got: '$CLEANUP_RETENTION_MONTHS'" >&2
  exit 1
fi

# ---------- Calculate cutoff date inside the app container ----------
CUTOFF=$(docker exec pm4py-llm-app python3 -c "
from datetime import date
from dateutil.relativedelta import relativedelta
import sys
months = int(sys.argv[1])
print((date.today() - relativedelta(months=months)).strftime('%Y%m%d'))
" "${CLEANUP_RETENTION_MONTHS}")

# ---------- Build the --apply flag string for child commands ----------
APPLY_FLAG=""
if [[ "$APPLY" == "true" ]]; then
  APPLY_FLAG="--apply"
fi

# ---------- Header helper ----------
separator() {
  echo "========================================================================"
}

# ---------- Run cleanup ----------
MODE_LABEL="dry-run"
if [[ "$APPLY" == "true" ]]; then
  MODE_LABEL="apply"
fi

echo
separator
echo "Cleanup mode    : ${MODE_LABEL}"
echo "Retention months: ${CLEANUP_RETENTION_MONTHS}"
echo "Cutoff date     : ${CUTOFF}"
separator

echo
separator
echo "==> app container (pm4py-llm-app)"
separator
docker exec pm4py-llm-app python3 -m utils.cleanup "${CUTOFF}" ${APPLY_FLAG}

echo
separator
echo "==> orchestrator container (pm4py-llm-orchestrator)"
separator
docker exec pm4py-llm-orchestrator python3 -m commands.cleanup "${CUTOFF}" ${APPLY_FLAG}

echo
separator
echo "Cleanup finished. Mode: ${MODE_LABEL} | Cutoff: ${CUTOFF}"
separator
