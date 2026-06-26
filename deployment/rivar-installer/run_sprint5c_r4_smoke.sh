#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/opt/rivar-demo"
COMPOSE_FILE="${INSTALL_DIR}/deployment/rivar-installer/docker-compose.rivar-demo.yml"

docker compose \
  --project-name rivar-demo \
  --env-file "${INSTALL_DIR}/.env" \
  -f "${COMPOSE_FILE}" \
  exec -T backend python /app/scripts/sprint5c_r4_runtime_smoke.py

echo "Sprint 5C-R4 smoke wrapper PASS"
