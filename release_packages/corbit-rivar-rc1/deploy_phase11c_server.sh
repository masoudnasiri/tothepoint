#!/bin/bash
# ============================================================================
# Phase 11C — Rivar UI Redesign Deploy Script (Linux Server)
# Target: /root/pdss_demo  |  COMPOSE_PROJECT_NAME=pdss_demo
# Run on: 193.162.129.58 as root
# ============================================================================
set -euo pipefail

DEPLOY_DIR="/root/pdss_demo"
COMPOSE_PROJECT="pdss_demo"
ARCHIVE="phase11c_ui_redesign_20260620.tar.gz"
BACKUP_DIR="/root/pdss_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "============================================================"
echo "  Phase 11C — Rivar UI Redesign System Migration Deploy"
echo "============================================================"
echo ""

# 1. Backup database before applying
echo "[1/5] Creating pre-deploy database backup..."
DB_SERVICE=$(COMPOSE_PROJECT_NAME=$COMPOSE_PROJECT docker compose -f $DEPLOY_DIR/docker-compose.yml config --services | grep -E "^(postgres|db)$" | head -1)
mkdir -p $BACKUP_DIR
DB_BACKUP="$BACKUP_DIR/pdss_demo_pre_phase11c_${TIMESTAMP}.sql"
COMPOSE_PROJECT_NAME=$COMPOSE_PROJECT docker compose -f $DEPLOY_DIR/docker-compose.yml exec -T "$DB_SERVICE" \
  pg_dump -U postgres procurement_dss > "$DB_BACKUP"
if [ ! -s "$DB_BACKUP" ]; then echo "[ERROR] Backup empty — aborting."; exit 1; fi
echo "  Backup: $DB_BACKUP"
echo ""

# 2. Extract Phase 11C archive to deployment path
echo "[2/5] Applying Phase 11C frontend source files..."
cd $DEPLOY_DIR
if [ -f "$ARCHIVE" ]; then
  tar -xzf "$ARCHIVE"
  echo "  Archive extracted."
else
  echo "[ERROR] Archive $ARCHIVE not found in $DEPLOY_DIR — upload it first via SCP."
  echo "  scp phase11c_ui_redesign_20260620.tar.gz root@193.162.129.58:$DEPLOY_DIR/"
  exit 1
fi
echo ""

# 3. Rebuild frontend container (no volume deletion)
echo "[3/5] Rebuilding frontend Docker image..."
COMPOSE_PROJECT_NAME=$COMPOSE_PROJECT docker compose -f $DEPLOY_DIR/docker-compose.yml up --build -d frontend
echo ""

# 4. Run quality gates
echo "[4/5] Running quality gates..."
echo ""

echo "--- Health check ---"
sleep 5
curl -sS http://127.0.0.1:18010/health
echo ""

echo "--- Backend full tests ---"
COMPOSE_PROJECT_NAME=$COMPOSE_PROJECT docker compose -f $DEPLOY_DIR/docker-compose.yml run --rm backend \
  python -m pytest tests -q
echo ""

echo "--- Phase 8 smoke tests ---"
COMPOSE_PROJECT_NAME=$COMPOSE_PROJECT docker compose -f $DEPLOY_DIR/docker-compose.yml run --rm backend \
  python -m pytest tests/test_phase8_release_candidate_smoke.py -q
echo ""

echo "--- Frontend build ---"
COMPOSE_PROJECT_NAME=$COMPOSE_PROJECT docker compose -f $DEPLOY_DIR/docker-compose.yml run --rm frontend \
  npm run build
echo ""

# 5. Verify containers are all up
echo "[5/5] Final container status..."
COMPOSE_PROJECT_NAME=$COMPOSE_PROJECT docker compose -f $DEPLOY_DIR/docker-compose.yml ps
echo ""

echo "============================================================"
echo "  Phase 11C deploy complete."
echo "  Verify UI at: http://193.162.129.58:13010"
echo "  See smoke checklist: docs/design/phase11c_ui_smoke_checklist.md"
echo "============================================================"
