# Phase 1 Migration - Linux Execution Guide

## Quick Start

```bash
# Make script executable
chmod +x execute_phase1_migrations.sh

# Run migrations
./execute_phase1_migrations.sh
```

## Prerequisites

1. **PostgreSQL client tools** (`psql`) must be installed
2. **SQL migration files** must be in the same directory as the script:
   - `create_procurement_packages_table.sql`
   - `create_package_subitems_table.sql`
   - `create_package_payments_table.sql`
   - `add_package_id_columns.sql`
   - `make_delivery_options_project_item_nullable.sql`
   - `add_supplier_id_to_supplier_payments.sql`
   - `increase_invoice_amount_precision.sql` (optional - will skip if already applied)
   - `add_procurement_options_check_constraint.sql`

3. **Database access** - You must have permissions to:
   - CREATE TABLE
   - ALTER TABLE
   - CREATE INDEX
   - CREATE CONSTRAINT

## Connection Methods

### Method 1: Docker Container (Recommended for Docker setups)

If your database runs in Docker, the script will auto-detect it. You can also force Docker mode:

**First, find your container name:**
```bash
docker ps | grep postgres
# or
docker ps --format "table {{.Names}}\t{{.Status}}" | grep postgres
```

**Then run with the correct container name:**
```bash
# Auto-detect Docker (will find any container with "postgres" in name)
export USE_DOCKER=true
export PGDATABASE=procurement_dss
export PGUSER=postgres

./execute_phase1_migrations.sh
```

**Or explicitly specify Docker container name (if auto-detection finds wrong one):**
```bash
export DOCKER_CONTAINER=pdss-postgres-1  # Your actual container name
export USE_DOCKER=true
export PGDATABASE=procurement_dss
export PGUSER=postgres

./execute_phase1_migrations.sh
```

### Method 2: Direct Connection (if port is exposed)

```bash
export PGHOST=localhost  # or your server IP
export PGPORT=5432
export PGDATABASE=procurement_dss
export PGUSER=postgres
export PGPASSWORD=postgres123

./execute_phase1_migrations.sh
```

### Method 3: DATABASE_URL (Full Connection String)

```bash
export DATABASE_URL="postgresql://postgres:password@localhost:5432/procurement_dss"

./execute_phase1_migrations.sh
```

### Method 4: Default Values (localhost with postgres user)

```bash
# Uses defaults: localhost:5432/procurement_dss as postgres
./execute_phase1_migrations.sh
```

### Method 5: Interactive Password Prompt

If `PGPASSWORD` is not set, `psql` will prompt for password interactively.

## What the Script Does

1. **Checks database connection** before starting
2. **Executes migrations in order** (1.1 through 1.8)
3. **Stops on first error** - won't continue if a migration fails
4. **Runs validation queries** after each successful migration
5. **Checks if migration 1.7 is already applied** (skips if precision is already NUMERIC(18,2))
6. **Provides colored output** for easy status tracking
7. **Generates summary** at the end with success/skip/fail counts

## Output

The script provides:
- ✅ **Green** - Successful operations
- ⚠️ **Yellow** - Warnings or skipped migrations
- ✗ **Red** - Errors or failures
- **Gray** - Informational messages

## Example Output

```
=== Phase 1 Migration Execution ===
Starting migrations at 2025-11-04 20:10:00

✓ Connected to localhost:5432/procurement_dss as postgres

Task 1.1: Create procurement_packages table
  File: create_procurement_packages_table.sql
  ✓ SUCCESS
  Running validation: Table structure
  [table structure output]
  Table exists. Current row count: 0

Task 1.2: Create package_subitems table
  ...
  
=== Migration Summary ===
Completed at 2025-11-04 20:10:05

SUCCESSFUL: 7
  ✓ Task 1.1: create_procurement_packages_table.sql
  ✓ Task 1.2: create_package_subitems_table.sql
  ...

SKIPPED: 1
  ⊘ Task 1.7: increase_invoice_amount_precision.sql

✅ All migrations completed successfully!
   Ready for Phase 2 (Data Migration)
```

## Error Handling

- Script uses `set -e` - exits immediately on any error
- If a migration fails, script stops and reports which task failed
- No partial migrations - all changes are within transactions (BEGIN/COMMIT)

## Troubleshooting

### Connection Errors

**If using Docker:**
```bash
# Check if container is running
docker ps | grep postgres

# Test connection via Docker
docker exec postgres psql -U postgres -d procurement_dss -c "SELECT version();"

# If container name is different, find it:
docker ps --format "table {{.Names}}\t{{.Status}}"
```

**If using direct connection:**
```bash
# Test connection manually
psql -h localhost -p 5432 -U postgres -d procurement_dss -c "SELECT version();"

# Or with DATABASE_URL
psql "$DATABASE_URL" -c "SELECT version();"
```

**Common Docker issues:**
- Container not running: `docker start postgres`
- Wrong container name: Check with `docker ps` and set `DOCKER_CONTAINER` environment variable
- Network issues: If on remote server, ensure Docker port is exposed or use Docker exec method

### Permission Errors

Ensure your database user has necessary permissions:
```sql
GRANT CREATE ON DATABASE procurement_dss TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA public TO postgres;
```

### File Not Found

Ensure all SQL files are in the same directory as the script:
```bash
ls -la *.sql
```

### Migration Already Applied

The script is idempotent - running it multiple times is safe:
- Uses `IF NOT EXISTS` for tables/columns
- Checks constraint existence before adding
- Skips migration 1.7 if already applied

## Verification After Execution

After successful execution, verify the changes:

```bash
# Check new tables
psql "$DATABASE_URL" -c "\dt procurement_packages package_subitems package_payments"

# Check package_id columns
psql "$DATABASE_URL" -c "SELECT table_name, column_name, is_nullable FROM information_schema.columns WHERE column_name = 'package_id' ORDER BY table_name;"

# Check CHECK constraints
psql "$DATABASE_URL" -c "SELECT table_name, constraint_name FROM information_schema.table_constraints WHERE constraint_name LIKE 'check_%' ORDER BY table_name;"
```

## Next Steps

After Phase 1 completes successfully, proceed with **Phase 2 (Data Migration)**:
- Create FULL packages for existing project items
- Link procurement_options to packages
- Migrate supplier_name to supplier_id
- Link financial records to packages

---

*Script Location: `backend/execute_phase1_migrations.sh`*  
*Last Updated: 2025-11-04*

