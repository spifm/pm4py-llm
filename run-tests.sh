#!/usr/bin/env bash
#
# Run the endpoint integration tests for every service INSIDE its Docker image.
# Nothing is installed on the host machine and nothing is installed at runtime:
# `pytest` and `httpx` are baked into the `test` stage of each Dockerfile.
# The one-off container is discarded afterwards (--rm).
#
# The external/heavy dependencies (pm4py, LLM clients, Moodle DB, Redis/RQ,
# Mermaid CLI, filesystem) are mocked by the tests, so no real services are
# required and `--no-deps` is used to avoid starting dependencies.
#
# Usage:
#   ./run-tests.sh                  # run all services
#   ./run-tests.sh mermaid-service  # run a single service
#
set -euo pipefail

cd "$(dirname "$0")"

COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.test.yml)

run_service_tests() {
  local service="$1"
  echo "========================================================================"
  echo "==> ${service}"
  echo "========================================================================"
  "${COMPOSE[@]}" build "${service}"
  "${COMPOSE[@]}" run --rm --no-deps --user root "${service}"
}

declare -a SERVICES=(
  app
  orchestrator
  moodle-data-service
  mermaid-service
  results-publisher
)

target="${1:-}"

for name in "${SERVICES[@]}"; do
  if [[ -z "${target}" || "${target}" == "${name}" ]]; then
    run_service_tests "${name}"
  fi
done

echo
echo "All requested endpoint integration tests passed."
