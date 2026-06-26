#!/usr/bin/env bash
# Run Sprint 5D procurement assignment runtime smoke inside demo backend container.
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/rivar-demo}"
COMPOSE_FILE="${INSTALL_DIR}/deployment/rivar-installer/docker-compose.rivar-demo.yml"
ENV_FILE="${INSTALL_DIR}/.env"

docker compose \
  --project-name rivar-demo \
  --env-file "${ENV_FILE}" \
  -f "${COMPOSE_FILE}" \
  exec -T backend \
  python scripts/sprint5d_procurement_assignment_runtime_smoke.py
