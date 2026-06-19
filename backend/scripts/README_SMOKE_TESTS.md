# Phase 3 Smoke Tests - Setup & Execution

## Prerequisites

1. **Dependencies Installed**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Database Connection**
   - Database must be running (PostgreSQL)
   - Connection configured via `DATABASE_URL` environment variable or `.env` file
   - Phase 2 migrations completed (packages exist)

3. **Environment Setup**
   - Ensure `.env` file exists with database connection
   - Or set `DATABASE_URL` environment variable

## Execution Methods

### Method 1: Direct Execution (Local Python)

```bash
cd backend
python scripts/smoke_test_phase3.py
```

### Method 2: Docker Container

If running in Docker:
```bash
docker-compose exec backend python scripts/smoke_test_phase3.py
```

### Method 3: Python Module

```bash
cd backend
python -m scripts.smoke_test_phase3
```

## Expected Output

The script will:
1. Display current feature flag states
2. Create or locate test data (project, item, supplier, package)
3. Run 5 test scenarios
4. Generate results files:
   - `backend/PHASE3_SMOKE_TEST_RESULTS.json`
   - `backend/PHASE3_SMOKE_TEST_RESULTS.md`

## Troubleshooting

### Error: "No module named 'sqlalchemy'"

**Solution**: Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Error: "Failed to import app modules"

**Solution**: Make sure you're in the backend directory
```bash
cd backend
python scripts/smoke_test_phase3.py
```

### Error: Database connection failed

**Solution**: Check database connection
- Verify `DATABASE_URL` in `.env` or environment
- Ensure PostgreSQL is running
- Check database credentials

### Error: "No packages found"

**Solution**: Run Phase 2 migrations first
```bash
cd backend
python run_phase2_data_migration.ps1  # Windows
# OR
./run_phase2_data_migration.sh       # Linux
```

## Exit Codes

- `0` - All tests passed
- `1` - One or more tests failed (check output for details)

