#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
INSTALL_DIR="/opt/rivar-demo"
COMPOSE_REL_PATH="deployment/rivar-installer/docker-compose.rivar-demo.yml"
ENV_EXAMPLE_REL_PATH="deployment/rivar-installer/.env.example"
BACKUP_ROOT="/root/rivar_demo_backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${BACKUP_ROOT}/pre_clean_install_${TIMESTAMP}"

FLAG_FRESH=0
FLAG_BACKUP_EXISTING=0
FLAG_WIPE_AFTER_BACKUP=0
FLAG_SEED_DEMO_DATA=0
BACKUP_DONE=0
DB_DUMP_PATH=""

usage() {
  cat <<'EOF'
Usage: install.sh [options]

Options:
  --fresh                         Fresh install mode.
  --backup-existing               Capture full backup before any cleanup.
  --wipe-existing-after-backup    Remove old pdss/rivar demo resources after backup.
  --seed-demo-data                Create deterministic Sprint 4A QA fixture.
  -h, --help                      Show this help.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --fresh) FLAG_FRESH=1 ;;
    --backup-existing) FLAG_BACKUP_EXISTING=1 ;;
    --wipe-existing-after-backup) FLAG_WIPE_AFTER_BACKUP=1 ;;
    --seed-demo-data) FLAG_SEED_DEMO_DATA=1 ;;
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

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

ensure_prerequisites() {
  require_command docker
  require_command tar
  if ! docker compose version >/dev/null 2>&1; then
    echo "Docker compose plugin is required." >&2
    exit 1
  fi
}

run_compose() {
  docker compose \
    --project-name rivar-demo \
    --env-file "${INSTALL_DIR}/.env" \
    -f "${INSTALL_DIR}/${COMPOSE_REL_PATH}" \
    "$@"
}

backup_existing() {
  mkdir -p "${BACKUP_DIR}"

  echo "Capturing docker state into ${BACKUP_DIR}"
  docker ps > "${BACKUP_DIR}/docker_ps.txt" || true
  docker ps -a > "${BACKUP_DIR}/docker_ps_all.txt" || true
  docker images > "${BACKUP_DIR}/docker_images.txt" || true
  docker volume ls > "${BACKUP_DIR}/docker_volumes.txt" || true
  docker network ls > "${BACKUP_DIR}/docker_networks.txt" || true

  if [ -d "/root/pdss_demo" ]; then
    tar -czf "${BACKUP_DIR}/root_pdss_demo.tar.gz" -C /root pdss_demo
  fi
  if [ -d "/opt/rivar-demo" ]; then
    tar -czf "${BACKUP_DIR}/opt_rivar_demo.tar.gz" -C /opt rivar-demo
  fi

  local pg_container=""
  pg_container="$(docker ps --format '{{.Names}}' | awk '/pdss_demo-postgres|rivar-demo-postgres|pdss-postgres/{print; exit}')"
  if [ -n "${pg_container}" ]; then
    DB_DUMP_PATH="${BACKUP_DIR}/postgres_dump.sql"
    if docker exec "${pg_container}" sh -lc 'pg_dumpall -U "${POSTGRES_USER:-postgres}"' > "${DB_DUMP_PATH}" 2>/dev/null; then
      echo "Database dump captured at ${DB_DUMP_PATH}"
    else
      DB_DUMP_PATH=""
      echo "Database dump was not captured (continuing)." >&2
    fi
  fi

  local front_name back_name
  front_name="$(docker ps --format '{{.Names}}' | awk '/frontend/{print; exit}')"
  back_name="$(docker ps --format '{{.Names}}' | awk '/backend/{print; exit}')"
  if [ -n "${front_name}" ]; then
    docker logs --tail 300 "${front_name}" > "${BACKUP_DIR}/frontend_logs_tail.txt" 2>&1 || true
  fi
  if [ -n "${back_name}" ]; then
    docker logs --tail 300 "${back_name}" > "${BACKUP_DIR}/backend_logs_tail.txt" 2>&1 || true
  fi

  BACKUP_DONE=1
}

wipe_existing_after_backup() {
  if [ "${BACKUP_DONE}" -ne 1 ]; then
    echo "Refusing wipe because backup has not completed." >&2
    exit 1
  fi

  if [ -f "/root/pdss_demo/docker-compose.yml" ]; then
    docker compose -f "/root/pdss_demo/docker-compose.yml" down --remove-orphans || true
  fi

  if [ -f "/opt/rivar-demo/${COMPOSE_REL_PATH}" ] && [ -f "/opt/rivar-demo/.env" ]; then
    docker compose --project-name rivar-demo --env-file "/opt/rivar-demo/.env" -f "/opt/rivar-demo/${COMPOSE_REL_PATH}" down --remove-orphans || true
  fi

  local containers
  containers="$(docker ps -aq --filter "name=pdss_demo-" --filter "name=pdss-" --filter "name=rivar-demo-")"
  if [ -n "${containers}" ]; then
    docker rm -f ${containers} || true
  fi

  local networks
  networks="$(docker network ls --format '{{.Name}}' | awk '/^pdss_demo|^rivar_demo|^rivar-demo/{print}')"
  if [ -n "${networks}" ]; then
    while IFS= read -r net_name; do
      [ -n "${net_name}" ] && docker network rm "${net_name}" >/dev/null 2>&1 || true
    done <<< "${networks}"
  fi

  local images
  images="$(docker images --format '{{.Repository}} {{.ID}}' | awk '/pdss_demo|rivar-demo/{print $2}' | sort -u)"
  if [ -n "${images}" ]; then
    while IFS= read -r image_id; do
      [ -n "${image_id}" ] && docker rmi "${image_id}" >/dev/null 2>&1 || true
    done <<< "${images}"
  fi

  if [ "${FLAG_FRESH}" -eq 1 ] && [ -d "/root/pdss_demo" ]; then
    rm -rf "/root/pdss_demo"
  fi

  if [ "${FLAG_FRESH}" -eq 1 ] && [ -n "${DB_DUMP_PATH}" ] && [ -f "${DB_DUMP_PATH}" ]; then
    docker volume rm pdss_demo_postgres_data >/dev/null 2>&1 || true
    docker volume rm rivar_demo_postgres_data >/dev/null 2>&1 || true
  fi
}

sync_source_to_install_dir() {
  if [ "${FLAG_FRESH}" -eq 1 ] && [ -d "${INSTALL_DIR}" ]; then
    rm -rf "${INSTALL_DIR}"
  fi
  mkdir -p "${INSTALL_DIR}"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
      --exclude ".git" \
      --exclude ".env" \
      "${SRC_ROOT}/" "${INSTALL_DIR}/"
  else
    tar -C "${SRC_ROOT}" --exclude ".git" --exclude ".env" -cf - . | tar -C "${INSTALL_DIR}" -xf -
  fi
}

ensure_env_file() {
  if [ "${FLAG_FRESH}" -eq 1 ]; then
    cp "${INSTALL_DIR}/${ENV_EXAMPLE_REL_PATH}" "${INSTALL_DIR}/.env"
  elif [ ! -f "${INSTALL_DIR}/.env" ]; then
    cp "${INSTALL_DIR}/${ENV_EXAMPLE_REL_PATH}" "${INSTALL_DIR}/.env"
  fi
}

wait_for_backend_health() {
  local attempts=40
  while [ "${attempts}" -gt 0 ]; do
    if run_compose ps backend | grep -q "healthy"; then
      return 0
    fi
    attempts=$((attempts - 1))
    sleep 3
  done
  echo "Backend did not become healthy in time." >&2
  run_compose ps
  return 1
}

run_install() {
  run_compose up -d --build
  wait_for_backend_health

  if [ "${FLAG_SEED_DEMO_DATA}" -eq 1 ]; then
    run_compose exec -T backend sh -lc "cd /app && PYTHONPATH=/app python scripts/create_sprint4a_demo_fixture.py --mode recreate"
  fi

  bash "${INSTALL_DIR}/deployment/rivar-installer/verify.sh"
}

ensure_prerequisites

if [ "${FLAG_BACKUP_EXISTING}" -eq 1 ]; then
  backup_existing
fi

if [ "${FLAG_WIPE_AFTER_BACKUP}" -eq 1 ]; then
  if [ "${FLAG_BACKUP_EXISTING}" -ne 1 ]; then
    echo "Refusing wipe because --backup-existing was not provided." >&2
    exit 1
  fi
  wipe_existing_after_backup
fi

sync_source_to_install_dir
ensure_env_file
run_install

echo "Install complete."
echo "Install directory: ${INSTALL_DIR}"
if [ "${BACKUP_DONE}" -eq 1 ]; then
  echo "Backup directory: ${BACKUP_DIR}"
fi
