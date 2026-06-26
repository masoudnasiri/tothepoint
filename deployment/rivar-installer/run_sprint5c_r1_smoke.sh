#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/opt/rivar-demo"
ENV_FILE="${INSTALL_DIR}/.env"
COMPOSE_FILE="${INSTALL_DIR}/deployment/rivar-installer/docker-compose.rivar-demo.yml"

# shellcheck disable=SC1090
source "${ENV_FILE}"

docker compose \
  --project-name rivar-demo \
  --env-file "${ENV_FILE}" \
  -f "${COMPOSE_FILE}" \
  exec -T \
  -e VERIFY_USERNAME="${VERIFY_USERNAME:-admin}" \
  -e VERIFY_PASSWORD="${VERIFY_PASSWORD:-admin123}" \
  backend \
  sh -lc 'cd /app && PYTHONPATH=/app python scripts/sprint5c_r1_runtime_smoke.py'
