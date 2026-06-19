# Phase 3 — Transition / Dual Mode Operation

**Status**: Implementation Complete  
**Date**: 2025-11-04  
**Last Updated**: 2025-11-04  
**Prerequisites**: Phase 1 (DDL) and Phase 2 (Data Migration) completed

## Executive Summary

Phase 3 implementation is **complete** and ready for testing. All core components have been implemented:

- ✅ Feature flags configuration (`backend/app/config.py`)
- ✅ Validation helpers for dual-mode operation (`backend/app/validators/package_validators.py`)
- ✅ Package service layer (`backend/app/services/package_service.py`)
- ✅ Audit and telemetry service (`backend/app/services/audit_service.py`)
- ✅ ORM models updated with `package_id` columns and `ProcurementPackage` model (`backend/app/models.py`)
- ✅ CRUD operations updated with dual-mode validation (`backend/app/crud.py`)
- ✅ API routers updated (`backend/app/routers/procurement.py`, `backend/app/routers/delivery_options.py`, `backend/app/routers/decisions.py`)
- ✅ Schemas updated with package_id fields (`backend/app/schemas.py`)
- ✅ Documentation updated (`backend/PHASE3_ROLLOUT_PLAN.md`)

**Next Steps**: Enable feature flags in staging environment, run smoke tests, and proceed to Phase 4 (Deprecation) after validation.

## Overview

Phase 3 introduces feature flags and application-layer updates to enable dual-mode operation where both package-based and legacy project-item-based flows coexist. This allows gradual migration without breaking existing functionality.

## Feature Flags

All feature flags are configured in `backend/app/config.py` and can be set via environment variables:

### Core Flags

1. **`ENABLE_PACKAGE_PROCUREMENT`** (default: `false`)
   - Enables package-aware procurement operations
   - When `true`, prefers `package_id` over `project_item_id`/`item_code`
   - Environment variable: `ENABLE_PACKAGE_PROCUREMENT=true`

2. **`LEGACY_PROJECT_ITEM_FALLBACK`** (default: `true`)
   - Allows legacy `project_item_id`/`item_code` operations when `package_id` not available
   - Should remain `true` during transition period
   - Environment variable: `LEGACY_PROJECT_ITEM_FALLBACK=true`

3. **`SUPPLIER_NORMALIZATION_ENFORCED`** (default: `false`)
   - Enforces `supplier_id` usage (blocks string-based `supplier_name` for new records)
   - Set to `true` after Phase 2 supplier migration is complete
   - Environment variable: `SUPPLIER_NORMALIZATION_ENFORCED=true`

### Advanced Flags

4. **`ENABLE_PACKAGE_BASED_OPTIMIZATION`** (default: `false`)
   - Enables package-aware optimization engine
   - Gradual rollout recommended
   - Environment variable: `ENABLE_PACKAGE_BASED_OPTIMIZATION=true`

5. **`REQUIRE_PACKAGE_ID_FOR_NEW_OPTIONS`** (default: `false`)
   - Stricter enforcement: requires `package_id` for new procurement options
   - Only enable after full migration
   - Environment variable: `REQUIRE_PACKAGE_ID_FOR_NEW_OPTIONS=true`

## Configuration

### Environment Variables

Add to `.env` or Docker Compose:

```bash
# Phase 3 Feature Flags
ENABLE_PACKAGE_PROCUREMENT=false
LEGACY_PROJECT_ITEM_FALLBACK=true
SUPPLIER_NORMALIZATION_ENFORCED=false
ENABLE_PACKAGE_BASED_OPTIMIZATION=false
REQUIRE_PACKAGE_ID_FOR_NEW_OPTIONS=false
```

### Code Access

```python
from app.config import settings

if settings.enable_package_procurement:
    # Use package-aware logic
    pass
else:
    # Use legacy logic
    pass
```

## Implementation Components

### 1. Feature Flags Configuration

**File**: `backend/app/config.py`

- Added 5 feature flags with environment variable support
- Defaults favor backward compatibility (legacy fallback enabled)

### 2. Validation Helpers

**File**: `backend/app/validators/package_validators.py`

**Functions**:
- `validate_package_or_legacy_reference()`: Ensures at least one reference (package_id, project_item_id, or item_code) is present
- `validate_supplier_reference()`: Validates supplier_id vs supplier_name based on flags
- `resolve_package_from_project_item()`: Resolves package_id from project_item_id
- `log_feature_flag_usage()`: Logs flag evaluations for telemetry

### 3. Package Service

**File**: `backend/app/services/package_service.py`

**Functions**:
- `get_package_for_project_item()`: Retrieves package information for a project item
- `get_package_subitems()`: Gets sub-items covered by a package
- `normalize_procurement_reference()`: Normalizes references to prefer package_id when enabled

### 4. Audit Service

**File**: `backend/app/services/audit_service.py`

**Functions**:
- `log_feature_flag_event()`: Logs feature flag evaluations to `migration_audit_log`
- `log_phase3_operation()`: Logs Phase 3 operations with dual-mode tracking

### 5. Schema Updates

**File**: `backend/app/schemas.py`

**Updated Schemas**:
- `ProcurementOptionBase`: Added `package_id` (optional)
- `ProcurementOptionCreate`: Supports both `package_id` and legacy references
- `ProcurementOptionUpdate`: Added `package_id` field
- `ProcurementOption`: Added `package_name` and `package_type` in response
- `DeliveryOptionCreate`: Supports both `package_id` and `project_item_id`
- `DeliveryOption`: Added `package_id` and `package_name` in response
- `FinalizedDecisionBase`: Added `package_id` (optional)
- `FinalizedDecision`: Added `package_name` and `package_type` in response

### 6. Router Updates (In Progress)

**Routers to Update**:
- `backend/app/routers/procurement.py`: Add package-aware validation
- `backend/app/routers/delivery_options.py`: Support `package_id` OR `project_item_id`
- `backend/app/routers/decisions.py`: Link decisions to packages

## Rollout Strategy

### Step 1: Enable Package Support (Non-Breaking)

```bash
# Enable package support but keep legacy fallback
ENABLE_PACKAGE_PROCUREMENT=true
LEGACY_PROJECT_ITEM_FALLBACK=true
SUPPLIER_NORMALIZATION_ENFORCED=false
```

**Expected Behavior**:
- New records can use `package_id` if provided
- Legacy records continue to work with `project_item_id`/`item_code`
- Both modes coexist

### Step 2: Enforce Supplier Normalization (After Phase 2)

```bash
# After supplier migration is complete
SUPPLIER_NORMALIZATION_ENFORCED=true
```

**Expected Behavior**:
- New records must use `supplier_id` (not `supplier_name`)
- Legacy records with `supplier_name` remain valid

### Step 3: Enable Package-Based Optimization (Gradual)

```bash
# Enable package-aware optimization
ENABLE_PACKAGE_BASED_OPTIMIZATION=true
```

**Expected Behavior**:
- Optimization engine uses package costs when available
- Falls back to legacy costs for records without packages

### Step 4: Require Package ID (Final Transition)

```bash
# Stricter enforcement (only after full migration)
REQUIRE_PACKAGE_ID_FOR_NEW_OPTIONS=true
```

**Expected Behavior**:
- New procurement options must have `package_id`
- Legacy creation paths disabled

## Validation Checklist

After enabling Phase 3 flags:

- [ ] Verify feature flags load correctly (`/api/config` or logs)
- [ ] Test procurement option creation with `package_id`
- [ ] Test procurement option creation with legacy `project_item_id`
- [ ] Test delivery option creation with both modes
- [ ] Verify supplier normalization enforcement (if enabled)
- [ ] Check `migration_audit_log` for flag evaluations
- [ ] Monitor API responses for `package_name`/`package_type` fields

## Validation Queries

### Check Feature Flag Usage

```sql
SELECT 
    migration_step,
    COUNT(*) as usage_count,
    MAX(created_at) as last_used
FROM migration_audit_log
WHERE migration_step LIKE 'phase3_%'
GROUP BY migration_step
ORDER BY last_used DESC;
```

### Check Dual-Mode Operations

```sql
SELECT 
    metadata->>'operation' as operation,
    metadata->>'record_type' as record_type,
    COUNT(*) FILTER (WHERE (metadata->>'used_package_id')::boolean) as used_package,
    COUNT(*) FILTER (WHERE (metadata->>'used_legacy_reference')::boolean) as used_legacy
FROM migration_audit_log
WHERE migration_step LIKE 'phase3_operation_%'
GROUP BY operation, record_type;
```

### Verify Package References

```sql
SELECT 
    'procurement_options' as table_name,
    COUNT(*) FILTER (WHERE package_id IS NOT NULL) as with_package_id,
    COUNT(*) FILTER (WHERE project_item_id IS NOT NULL) as with_project_item_id,
    COUNT(*) FILTER (WHERE package_id IS NULL AND project_item_id IS NULL) as orphaned
FROM procurement_options
UNION ALL
SELECT 
    'delivery_options',
    COUNT(*) FILTER (WHERE package_id IS NOT NULL),
    COUNT(*) FILTER (WHERE project_item_id IS NOT NULL),
    COUNT(*) FILTER (WHERE package_id IS NULL AND project_item_id IS NULL)
FROM delivery_options
UNION ALL
SELECT 
    'finalized_decisions',
    COUNT(*) FILTER (WHERE package_id IS NOT NULL),
    COUNT(*) FILTER (WHERE project_item_id IS NOT NULL),
    0
FROM finalized_decisions;
```

## Rollback Procedure

If issues occur during Phase 3 rollout:

1. **Disable Feature Flags**:
   ```bash
   ENABLE_PACKAGE_PROCUREMENT=false
   ENABLE_PACKAGE_BASED_OPTIMIZATION=false
   REQUIRE_PACKAGE_ID_FOR_NEW_OPTIONS=false
   ```

2. **Restart Application**: Restart backend service to reload config

3. **Verify Legacy Mode**: All operations should fall back to legacy paths

4. **No Database Changes**: Phase 3 is application-layer only; no rollback needed

## Testing

### Smoke Tests

**Script**: `backend/scripts/smoke_test_phase3.py`

**Prerequisites**:
- Install dependencies: `pip install -r requirements.txt`
- Database connection configured (DATABASE_URL or .env)
- Phase 2 migrations completed (packages exist)

**Run**:
```bash
cd backend
python scripts/smoke_test_phase3.py
```

**Or in Docker**:
```bash
docker-compose exec backend python scripts/smoke_test_phase3.py
```

**See**: `backend/scripts/README_SMOKE_TESTS.md` for detailed setup instructions.

**Output**:
- `backend/PHASE3_SMOKE_TEST_RESULTS.json` - JSON results
- `backend/PHASE3_SMOKE_TEST_RESULTS.md` - Markdown report

**What it tests**:
- Procurement option creation with `package_id` (package-first)
- Procurement option creation with `project_item_id` (legacy fallback)
- Delivery option creation with `package_id`
- Delivery option creation with `project_item_id` (legacy fallback)
- Supplier normalization (supplier_id vs supplier_name)

**Exit codes**:
- `0` - All tests passed
- `1` - One or more tests failed

### Automated Tests

**Location**: `backend/tests/`

**Run**:
```bash
cd backend
pytest tests/ -v
```

**Test files**:
- `test_validators.py` - Unit tests for validation helpers
- `test_crud_phase3.py` - Integration tests for CRUD operations
- `test_api_phase3.py` - API endpoint tests

**Coverage**:
- Package vs legacy reference validation
- Supplier normalization paths
- Dual-mode CRUD operations
- API response validation

**Requirements**:
- `pytest`
- `pytest-asyncio`
- `httpx` (for API tests)

**Note**: Tests use in-memory SQLite database for isolation.

### Manual Testing

1. **Create Procurement Option**:
   - With `package_id`: Should succeed if flag enabled
   - With `project_item_id`: Should succeed (legacy fallback)
   - With both: Should prefer `package_id` if flag enabled

2. **Create Delivery Option**:
   - With `package_id`: Should succeed if flag enabled
   - With `project_item_id`: Should succeed (legacy fallback)

3. **Supplier Normalization**:
   - With `supplier_id`: Should succeed
   - With `supplier_name`: Should succeed if flag not enforced, fail if enforced

## Monitoring

### Logs to Watch

- Feature flag evaluations: `Feature flag evaluation: ENABLE_PACKAGE_PROCUREMENT=...`
- Phase 3 operations: `phase3_operation_*` in `migration_audit_log`
- Validation errors: `400 Bad Request` for missing references

### Metrics to Track

- Percentage of records using `package_id` vs legacy references
- Feature flag evaluation counts
- Dual-mode operation success rates

## Next Steps (Phase 4)

After Phase 3 is stable, proceed to Phase 4 deprecation and enforcement.

**See**: `backend/PHASE4_ROLLOUT_PROMPT.md` for detailed Phase 4 planning.

Phase 4 will:
1. **Enforce NOT NULL Constraints**: Make `package_id` required for new records
2. **Deprecate Legacy Fields**: Remove `project_item_id`/`item_code` dependencies
3. **Enforce Supplier Normalization**: Make `supplier_id` required
4. **Frontend Migration**: Update UI to use package_id exclusively
5. **Cleanup**: Remove deprecated fields after migration period

## Troubleshooting

### Issue: Feature flags not loading

**Solution**: Check environment variables are set correctly and restart backend

### Issue: Validation errors on legacy operations

**Solution**: Ensure `LEGACY_PROJECT_ITEM_FALLBACK=true`

### Issue: Package ID not resolving

**Solution**: Verify Phase 2 migration created FULL packages for project items

### Issue: Supplier normalization blocking operations

**Solution**: Ensure Phase 2 supplier migration completed, or set `SUPPLIER_NORMALIZATION_ENFORCED=false`

### Issue: Audit logging failures

**Fixed (2025-11-04)**: Audit logging was failing with SQL syntax errors. The fix changed parameter binding from positional tuples to named dictionary parameters and updated the JSON casting syntax. See `backend/PHASE3_SMOKE_TEST_RESULTS.md` for details.

---

**End of Phase 3 Rollout Plan**

*Ready for gradual rollout. All flags default to backward-compatible values.*

**Last Updated**: 2025-11-04 (Audit logging fix applied, smoke tests passing)

