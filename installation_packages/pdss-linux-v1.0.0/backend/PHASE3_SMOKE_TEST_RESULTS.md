# Phase 3 Smoke Test Results

**Test Run**: 2025-11-04 21:10:51

## Flag States

- `ENABLE_PACKAGE_PROCUREMENT`: `False`
- `LEGACY_PROJECT_ITEM_FALLBACK`: `True`
- `SUPPLIER_NORMALIZATION_ENFORCED`: `False`
- `ENABLE_PACKAGE_BASED_OPTIMIZATION`: `False`
- `REQUIRE_PACKAGE_ID_FOR_NEW_OPTIONS`: `False`

## Test Scenarios

### Procurement Option - Package First - ✅ PASS
**Time**: 2025-11-04T21:10:53.280262
- **package_id**: 1
- **project_item_id**: None
- **supplier_id**: 3
- **option_id**: 47
- **flag_enabled**: False

### Procurement Option - Legacy Fallback - ✅ PASS
**Time**: 2025-11-04T21:10:53.384815
- **package_id**: None
- **project_item_id**: 18
- **supplier_id**: 3
- **option_id**: 48
- **package_resolved**: False

### Delivery Option - Package First - ✅ PASS
**Time**: 2025-11-04T21:10:53.433286
- **package_id**: 1
- **project_item_id**: 18
- **option_id**: 54
- **flag_enabled**: False

### Delivery Option - Legacy Fallback - ✅ PASS
**Time**: 2025-11-04T21:10:53.472482
- **package_id**: None
- **project_item_id**: 18
- **option_id**: 55
- **package_resolved**: False

### Supplier Normalization - ✅ PASS
**Time**: 2025-11-04T21:10:53.543990
- **supplier_id_test**: True
- **supplier_name_test**: True
- **normalization_enforced**: False

## Summary

- **Total Scenarios**: 5
- **Passed**: 5
- **Failed**: 0
- **Warnings**: 0
- **Errors**: 0

## Successful Validation Run (2025-11-04 21:10:51)

**Status**: ✅ All scenarios passed after audit logging fix

**Flag States Used**:
- `ENABLE_PACKAGE_PROCUREMENT`: `False`
- `LEGACY_PROJECT_ITEM_FALLBACK`: `True`
- `SUPPLIER_NORMALIZATION_ENFORCED`: `False`
- `ENABLE_PACKAGE_BASED_OPTIMIZATION`: `False`
- `REQUIRE_PACKAGE_ID_FOR_NEW_OPTIONS`: `False`

**Test Command**: `docker-compose exec backend python scripts/smoke_test_phase3.py`

**Result**: Exit code 0, all 5 scenarios passed successfully

**Audit Logging**: All audit log inserts completed successfully without errors. The fix to use named parameters with dictionary binding and `CAST(:metadata AS jsonb)` resolved the previous SQL syntax errors.
