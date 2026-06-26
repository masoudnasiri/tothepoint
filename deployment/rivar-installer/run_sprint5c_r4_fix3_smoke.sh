#!/usr/bin/env bash
set -euo pipefail
INSTALL_DIR="/opt/rivar-demo"
bash "${INSTALL_DIR}/deployment/rivar-installer/run_sprint5c_r4_smoke.sh"
docker compose --project-name rivar-demo \
  --env-file "${INSTALL_DIR}/.env" \
  -f "${INSTALL_DIR}/deployment/rivar-installer/docker-compose.rivar-demo.yml" \
  exec -T backend python /app/scripts/sprint5c_r4_fix3_runtime_smoke.py
