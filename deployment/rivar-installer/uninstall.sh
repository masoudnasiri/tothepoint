#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/opt/rivar-demo"
COMPOSE_REL_PATH="deployment/rivar-installer/docker-compose.rivar-demo.yml"
ENV_FILE="${INSTALL_DIR}/.env"
COMPOSE_FILE="${INSTALL_DIR}/${COMPOSE_REL_PATH}"
WIPE_DATA=0

usage() {
  cat <<'EOF'
Usage: uninstall.sh [options]

Options:
  --wipe-data   Remove rivar_demo_postgres_data volume.
  -h, --help    Show this help.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --wipe-data) WIPE_DATA=1 ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      usage
      exit 1
      ;;
  esac
done

if [ ! -f "${COMPOSE_FILE}" ] || [ ! -f "${ENV_FILE}" ]; then
  echo "Compose file or .env not found in ${INSTALL_DIR}" >&2
  exit 1
fi

docker compose \
  --project-name rivar-demo \
  --env-file "${ENV_FILE}" \
  -f "${COMPOSE_FILE}" \
  down --remove-orphans

if [ "${WIPE_DATA}" -eq 1 ]; then
  docker volume rm rivar_demo_postgres_data >/dev/null 2>&1 || true
  echo "Volume rivar_demo_postgres_data removed."
fi

echo "Uninstall complete. Backups were not modified."
