#!/usr/bin/env bash
# Sprint 5E-R4: finalized-only procurement assignment item visibility.
set -euo pipefail

INSTALL_DIR="/opt/rivar-demo"
COMPOSE_FILE="${INSTALL_DIR}/deployment/rivar-installer/docker-compose.rivar-demo.yml"
ENV_FILE="${INSTALL_DIR}/.env"
DEPLOY_COMMIT="${1:?commit hash required}"
DEPLOY_BRANCH="${2:-restart/sprint5e-r4-finalized-only-assignment-items}"
DEPLOYED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "=== Rivar demo update deploy (5E-R4) ==="
echo "Branch: ${DEPLOY_BRANCH}"
echo "Commit: ${DEPLOY_COMMIT}"

cd "${INSTALL_DIR}"

docker run --rm -v "${INSTALL_DIR}/deployment/rivar-installer:/d" alpine:3.20 \
  sh -c 'apk add --no-cache dos2unix >/dev/null && dos2unix /d/*.sh'

mkdir -p docs/restart-audit
printf 'branch=%s\ncommit=%s\ndeployed_at=%s\nsprint=5E-R4\n' \
  "${DEPLOY_BRANCH}" "${DEPLOY_COMMIT}" "${DEPLOYED_AT}" \
  > DEPLOYED_COMMIT.txt

# Keep docs marker mirrored to avoid provenance divergence.
cp DEPLOYED_COMMIT.txt docs/restart-audit/DEPLOYED_COMMIT.txt

docker compose \
  --project-name rivar-demo \
  --env-file "${ENV_FILE}" \
  -f "${COMPOSE_FILE}" \
  build --no-cache backend frontend

docker compose \
  --project-name rivar-demo \
  --env-file "${ENV_FILE}" \
  -f "${COMPOSE_FILE}" \
  up -d backend frontend

attempts=40
while [ "${attempts}" -gt 0 ]; do
  if docker compose --project-name rivar-demo --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" ps backend | grep -q "healthy"; then
    break
  fi
  attempts=$((attempts - 1))
  sleep 3
done

bash "${INSTALL_DIR}/deployment/rivar-installer/run_sprint5d_smoke.sh"
echo "Deploy rebuild complete."
