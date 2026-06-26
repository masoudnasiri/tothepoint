#!/usr/bin/env bash
# Apply accepted idempotent R3 schema migrations to the demo Postgres database.
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/rivar-demo}"
COMPOSE_REL_PATH="${COMPOSE_REL_PATH:-deployment/rivar-installer/docker-compose.rivar-demo.yml}"
ENV_FILE="${INSTALL_DIR}/.env"
COMPOSE_FILE="${INSTALL_DIR}/${COMPOSE_REL_PATH}"

if [ ! -f "${COMPOSE_FILE}" ] || [ ! -f "${ENV_FILE}" ]; then
  echo "Compose file or .env not found in ${INSTALL_DIR}" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "${ENV_FILE}"

run_psql_file() {
  local sql_file="$1"
  if [ ! -f "${sql_file}" ]; then
    echo "Migration file not found: ${sql_file}" >&2
    exit 1
  fi
  echo "Applying schema migration: ${sql_file}"
  docker compose \
    --project-name rivar-demo \
    --env-file "${ENV_FILE}" \
    -f "${COMPOSE_FILE}" \
    exec -T postgres \
    psql -v ON_ERROR_STOP=1 -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
    < "${sql_file}"
}

# Canonical Sprint 3A-R3 migrations (idempotent; do not duplicate DDL elsewhere).
run_psql_file "${INSTALL_DIR}/backend/add_procurement_cost_component_payment_metadata.sql"

echo "R3 schema migrations applied."
