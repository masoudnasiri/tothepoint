#!/bin/bash
cd "$(dirname "$0")/.."
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "Creating database backup..."
docker-compose exec -T db pg_dump -U postgres procurement_dss > "$BACKUP_DIR/db_backup_$DATE.sql"

echo "Backup saved: $BACKUP_DIR/db_backup_$DATE.sql"

# Keep only last 30 days
find "$BACKUP_DIR" -name "*.sql" -mtime +30 -delete