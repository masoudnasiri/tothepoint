# Migration: Add main_item_quantity Column

This migration adds the `main_item_quantity` column to the `procurement_packages` table.

## Quick Start

### Option 1: Using Docker (Recommended)

```bash
# Auto-detect PostgreSQL container
USE_DOCKER=true ./apply_main_item_quantity_migration.sh

# Or specify container name
DOCKER_CONTAINER=pdss-postgres-1 ./apply_main_item_quantity_migration.sh
```

### Option 2: Direct Database Connection

```bash
# Using environment variables
DB_HOST=localhost \
DB_PORT=5432 \
DB_NAME=procurement_dss \
DB_USER=postgres \
DB_PASSWORD=your_password \
./apply_main_item_quantity_migration.sh

# Or using DATABASE_URL
DATABASE_URL="postgresql://postgres:password@localhost:5432/procurement_dss" \
./apply_main_item_quantity_migration.sh
```

## Prerequisites

1. **Linux/Unix system** with bash shell
2. **PostgreSQL client** (`psql`) OR **Docker** installed
3. **Database access** credentials
4. **Migration file** (`add_main_item_quantity_column.sql`) in the same directory

## Usage

1. **Make script executable** (if needed):
   ```bash
   chmod +x apply_main_item_quantity_migration.sh
   ```

2. **Run the script**:
   ```bash
   ./apply_main_item_quantity_migration.sh
   ```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_NAME` | Database name | `procurement_dss` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | `postgres` |
| `USE_DOCKER` | Use Docker execution | `false` |
| `DOCKER_CONTAINER` | Docker container name | Auto-detected |

## What the Migration Does

1. **Checks** if the `main_item_quantity` column already exists
2. **Adds** the column if it doesn't exist:
   - Type: `INTEGER`
   - Nullable: `YES`
   - Default: `0`
3. **Adds** a comment describing the column
4. **Verifies** the migration was successful

## Output

The script provides:
- ✅ Colored status messages
- 📝 Detailed log file (`migration_main_item_quantity.log`)
- ✓ Verification of column existence

## Troubleshooting

### Error: "Migration file not found"
- Ensure `add_main_item_quantity_column.sql` is in the same directory as the script

### Error: "psql command not found"
- Install PostgreSQL client: `sudo apt-get install postgresql-client`
- Or use Docker mode: `USE_DOCKER=true ./apply_main_item_quantity_migration.sh`

### Error: "Docker container not found"
- List containers: `docker ps`
- Set container name: `DOCKER_CONTAINER=your-container-name ./apply_main_item_quantity_migration.sh`

### Error: "Connection refused"
- Check database is running
- Verify connection parameters (host, port, credentials)
- Check firewall settings

## Safety Features

- ✅ **Idempotent**: Safe to run multiple times
- ✅ **Transaction-based**: Uses BEGIN/COMMIT for atomicity
- ✅ **Verification**: Confirms migration success
- ✅ **Logging**: All operations logged to file

## Rollback

To remove the column (if needed):

```sql
ALTER TABLE procurement_packages DROP COLUMN IF EXISTS main_item_quantity;
```

**Note**: Only rollback if you're sure no data depends on this column.

