#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/opt/rivar-demo"
COMPOSE_REL_PATH="deployment/rivar-installer/docker-compose.rivar-demo.yml"
ENV_FILE="${INSTALL_DIR}/.env"
COMPOSE_FILE="${INSTALL_DIR}/${COMPOSE_REL_PATH}"
BACKEND_URL="http://127.0.0.1:8000"
FRONTEND_URL="http://127.0.0.1:3000"
ENSURE_FIXTURE=1

usage() {
  cat <<'EOF'
Usage: verify.sh [options]

Options:
  --backend-url URL   Backend base URL (default http://127.0.0.1:8000)
  --frontend-url URL  Frontend base URL (default http://127.0.0.1:3000)
  --no-ensure-fixture Skip deterministic fixture (re)seed step before verification.
  -h, --help          Show this help.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --backend-url)
      BACKEND_URL="$2"
      shift 2
      ;;
    --frontend-url)
      FRONTEND_URL="$2"
      shift 2
      ;;
    --no-ensure-fixture)
      ENSURE_FIXTURE=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [ ! -f "${COMPOSE_FILE}" ] || [ ! -f "${ENV_FILE}" ]; then
  echo "Compose file or .env not found in ${INSTALL_DIR}" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "${ENV_FILE}"

echo "Checking frontend routes..."
curl -fsS -o /dev/null "${FRONTEND_URL}/"
curl -fsS -o /dev/null -H "Accept: text/html" "${FRONTEND_URL}/login"
curl -fsS -o /dev/null -H "Accept: text/html" "${FRONTEND_URL}/procurement"
curl -fsS -o /dev/null "${FRONTEND_URL}/asset-manifest.json"

echo "Checking backend health and OpenAPI..."
curl -fsS -o /dev/null "${BACKEND_URL}/health"
curl -fsS -o /dev/null "${BACKEND_URL}/openapi.json"

echo "Checking compose services..."
docker compose --project-name rivar-demo --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" ps

if [ "${ENSURE_FIXTURE}" -eq 1 ]; then
  echo "Seeding deterministic verification fixture..."
  docker compose \
    --project-name rivar-demo \
    --env-file "${ENV_FILE}" \
    -f "${COMPOSE_FILE}" \
    exec -T backend \
    sh -lc "cd /app && PYTHONPATH=/app python scripts/create_sprint4a_demo_fixture.py --mode recreate"
fi

echo "Running Sprint 3A-R3 backend runtime verification..."
docker compose \
  --project-name rivar-demo \
  --env-file "${ENV_FILE}" \
  -f "${COMPOSE_FILE}" \
  exec -T backend \
  sh -lc "cd /app && PYTHONPATH=/app python scripts/verify_runtime_r3.py --backend-url http://127.0.0.1:8000 --username '${VERIFY_USERNAME:-admin}' --password '${VERIFY_PASSWORD:-admin123}'"

echo "Verification PASS."
