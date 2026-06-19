# Phase 4 — Deprecation & Enforcement

**Status**: Planning  
**Prerequisites**: Phase 1 (DDL), Phase 2 (Data Migration), Phase 3 (Dual Mode) completed  
**Reference**: `FUTURE_STATE_PROCUREMENT_MODEL.md`

## Context

Phases 1-3 have successfully implemented the package-based procurement system with dual-mode operation. Phase 4 focuses on deprecating legacy fields and enforcing package-first operations.

### Current State (Post-Phase 3)

- ✅ Package tables and columns exist (Phase 1)
- ✅ Data migrated to packages (Phase 2)
- ✅ Dual-mode operation functional (Phase 3)
- ✅ Feature flags control behavior
- ✅ Backward compatibility preserved

### Phase 4 Goals

1. **Enforce NOT NULL Constraints**: Make `package_id` required for new records
2. **Deprecate Legacy Fields**: Remove `project_item_id`/`item_code` dependencies from new records
3. **Supplier Normalization**: Enforce `supplier_id` requirement, deprecate `supplier_name`
4. **Frontend Migration**: Update frontend to use `package_id` exclusively
5. **Cleanup**: Remove deprecated fields and constraints after migration period

## Deliverables

### 1. Database Migrations

**SQL Migration Scripts** (under `backend/`):

1. `enforce_package_id_not_null.sql`
   - Add NOT NULL constraint to `package_id` in `procurement_options` (new records)
   - Add NOT NULL constraint to `package_id` in `delivery_options` (new records)
   - Add NOT NULL constraint to `package_id` in `finalized_decisions` (new records)
   - Use `ALTER TABLE ... ADD CONSTRAINT ... NOT NULL` with `CHECK` for existing NULL values

2. `enforce_supplier_id_not_null.sql`
   - Add NOT NULL constraint to `supplier_id` in `procurement_options`
   - Add NOT NULL constraint to `supplier_id` in `supplier_payments`
   - Migrate remaining `supplier_name` references to `supplier_id`

3. `deprecate_legacy_fields.sql`
   - Add deprecation comments to `project_item_id`, `item_code` in `procurement_options`
   - Add deprecation comments to `project_item_id` in `delivery_options`
   - Add deprecation comments to `supplier_name` fields
   - Create migration audit entries

4. `remove_legacy_constraints.sql` (final cleanup)
   - Remove CHECK constraints that allowed legacy fields
   - Add final NOT NULL constraints after migration period
   - Document removal plan

### 2. Application Layer Updates

**Files to Update**:

1. **`backend/app/config.py`**
   - Remove `LEGACY_PROJECT_ITEM_FALLBACK` flag (default to `false`)
   - Set `ENABLE_PACKAGE_PROCUREMENT` default to `true`
   - Set `SUPPLIER_NORMALIZATION_ENFORCED` default to `true`
   - Add deprecation warnings for legacy field usage

2. **`backend/app/validators/package_validators.py`**
   - Require `package_id` when `ENABLE_PACKAGE_PROCUREMENT=true`
   - Block `project_item_id`/`item_code` for new records
   - Enforce `supplier_id` requirement

3. **`backend/app/crud.py`**
   - Remove legacy fallback logic
   - Require `package_id` for new procurement/delivery options
   - Require `supplier_id` for new records

4. **`backend/app/routers/*.py`**
   - Update endpoints to require `package_id`
   - Return deprecation warnings in responses for legacy fields
   - Update API documentation

5. **`backend/app/schemas.py`**
   - Mark legacy fields as deprecated in Pydantic models
   - Add validation warnings
   - Update response schemas

### 3. Frontend Updates

**Files to Update** (if applicable):

1. **`frontend/src/api/api.ts`**
   - Update API calls to use `package_id` instead of `project_item_id`
   - Remove legacy field handling

2. **`frontend/src/components/*.tsx`**
   - Update forms to use package selection
   - Remove legacy item code/project item selection
   - Update display components

3. **`frontend/src/i18n/*.json`**
   - Update translation keys for package-based UI

### 4. Testing & Validation

**Test Coverage**:

1. **Unit Tests**
   - Test NOT NULL constraint enforcement
   - Test legacy field rejection
   - Test supplier_id requirement

2. **Integration Tests**
   - Test migration scripts
   - Test application layer enforcement
   - Test API endpoint validation

3. **Smoke Tests**
   - Verify package-first operations
   - Verify legacy field rejection
   - Verify supplier normalization

4. **Data Validation**
   - Verify all records have `package_id`
   - Verify all records have `supplier_id`
   - Verify no orphaned legacy references

### 5. Documentation

**Documents to Create/Update**:

1. **`backend/PHASE4_ROLLOUT_PLAN.md`**
   - Detailed migration steps
   - Rollout schedule
   - Rollback procedures
   - Validation checklist

2. **`backend/PHASE4_MIGRATION_SUMMARY.md`**
   - Migration execution log
   - Validation results
   - Issues and resolutions

3. **API Documentation**
   - Update OpenAPI/Swagger docs
   - Document deprecation timeline
   - Migration guide for API consumers

## Migration Strategy

### Phase 4.1: Enforcement (Gradual)

1. **Enable Strict Flags**
   ```bash
   ENABLE_PACKAGE_PROCUREMENT=true
   LEGACY_PROJECT_ITEM_FALLBACK=false
   SUPPLIER_NORMALIZATION_ENFORCED=true
   REQUIRE_PACKAGE_ID_FOR_NEW_OPTIONS=true
   ```

2. **Add NOT NULL Constraints** (with default values for existing NULL)
   - Use `DEFAULT` values or backfill before constraint
   - Apply constraints in batches

3. **Update Application Layer**
   - Require `package_id` in validators
   - Return 400 errors for legacy field usage
   - Log deprecation warnings

### Phase 4.2: Frontend Migration

1. **Update Frontend Components**
   - Replace project item selection with package selection
   - Update API calls
   - Test end-to-end workflows

2. **Gradual Rollout**
   - Feature flag for new UI
   - A/B testing if needed
   - Monitor for issues

### Phase 4.3: Cleanup (Final)

1. **Remove Legacy Fields** (after migration period)
   - Drop `project_item_id`, `item_code` from `procurement_options`
   - Drop `project_item_id` from `delivery_options` (keep nullable for backward compatibility initially)
   - Drop `supplier_name` fields
   - Remove legacy CHECK constraints

2. **Final Validation**
   - Verify all operations use package_id
   - Verify no legacy field references
   - Performance testing

## Rollback Procedure

If issues occur during Phase 4:

1. **Revert Feature Flags**
   ```bash
   LEGACY_PROJECT_ITEM_FALLBACK=true
   REQUIRE_PACKAGE_ID_FOR_NEW_OPTIONS=false
   ```

2. **Relax Constraints**
   - Make `package_id` nullable again (if needed)
   - Allow legacy field usage

3. **Rollback Migrations**
   - Remove NOT NULL constraints
   - Restore CHECK constraints

4. **Revert Application Code**
   - Restore legacy fallback logic
   - Re-enable legacy field acceptance

## Validation Checklist

- [ ] All new records have `package_id` set
- [ ] All new records have `supplier_id` set
- [ ] No new records use `project_item_id`/`item_code` (procurement_options)
- [ ] No new records use `supplier_name`
- [ ] Frontend uses package selection exclusively
- [ ] API endpoints reject legacy fields
- [ ] Audit logs show package-first operations
- [ ] Performance benchmarks met
- [ ] No regression in existing functionality

## Timeline Estimate

- **Phase 4.1 (Enforcement)**: 1-2 weeks
- **Phase 4.2 (Frontend Migration)**: 2-3 weeks
- **Phase 4.3 (Cleanup)**: 1 week
- **Total**: 4-6 weeks

## Dependencies

- Phase 3 validation complete
- Frontend team availability
- Database maintenance window for constraint changes
- User acceptance testing

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing workflows | Gradual rollout with feature flags |
| Data migration issues | Comprehensive validation before constraints |
| Frontend compatibility | Parallel UI support during transition |
| Performance degradation | Benchmark before/after |
| User confusion | Clear documentation and training |

## Success Criteria

- ✅ All new records use `package_id` exclusively
- ✅ All new records use `supplier_id` exclusively
- ✅ No legacy field dependencies in new code
- ✅ Frontend fully migrated to package-based UI
- ✅ Performance maintained or improved
- ✅ Zero production incidents during migration

## Next Steps

1. Review and approve Phase 4 plan
2. Schedule database maintenance window
3. Coordinate with frontend team
4. Create migration scripts
5. Run smoke tests in staging
6. Execute Phase 4.1 (Enforcement)
7. Execute Phase 4.2 (Frontend Migration)
8. Execute Phase 4.3 (Cleanup)
9. Final validation and documentation

---

**Ready for implementation after Phase 3 validation complete.**

