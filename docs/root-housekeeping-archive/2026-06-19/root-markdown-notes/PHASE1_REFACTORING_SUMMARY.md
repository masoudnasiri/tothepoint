# Phase 1 - Database Schema Refactoring Summary

## Overview
This document summarizes the comprehensive database schema refactoring completed for the Procurement Decision Support System (DSS). The refactoring transforms the system from an abstract time-slot based approach to a real-world calendar-based system with comprehensive cash-flow tracking and decision management.

## Completed Changes

### 1. New Database Models

#### ProjectPhase Model
**File:** `backend/app/models.py`

A new model to replace abstract time slots with structured project phases linked to actual calendar dates:
- `id`: Primary Key (Integer)
- `project_id`: Foreign Key to Project (Integer, non-nullable)
- `phase_name`: String (e.g., "Q1-2025", "Foundation Stage")
- `start_date`: Date (non-nullable)
- `end_date`: Date (non-nullable)
- `created_at`, `updated_at`: Timestamps

**Relationship:** Bidirectional relationship with Project model via `phases` attribute.

#### OptimizationRun Model
**File:** `backend/app/models.py`

Tracks optimization execution history separately from results:
- `run_id`: UUID Primary Key
- `run_timestamp`: DateTime with default to current UTC time
- `request_parameters`: JSON (stores input parameters)
- `status`: String ('SUCCESS', 'FAILED', 'IN_PROGRESS')

**Relationship:** One-to-many with FinalizedDecision.

#### FinalizedDecision Model
**File:** `backend/app/models.py`

Tracks user decisions, distinguishing them from optimization suggestions:
- `id`: Primary Key (Integer)
- `project_item_id`: Foreign Key to ProjectItem (non-nullable)
- `procurement_option_id`: Foreign Key to ProcurementOption (non-nullable)
- `run_id`: Foreign Key to OptimizationRun (nullable)
- `decision_maker_id`: Foreign Key to User (non-nullable)
- `decision_date`: DateTime (non-nullable)
- `is_manual_edit`: Boolean (default: False)
- `notes`: Text (nullable)
- `created_at`, `updated_at`: Timestamps

**Relationships:** Links to ProjectItem, ProcurementOption, OptimizationRun, and User.

#### DecisionFactorWeight Model
**File:** `backend/app/models.py`

Stores optimization factor weights for the decision engine:
- `id`: Primary Key (Integer)
- `factor_name`: String (unique, non-nullable)
- `weight`: Integer (non-nullable, default: 5, range: 1-10)
- `description`: Text (nullable)
- `created_at`, `updated_at`: Timestamps

**Constraint:** Check constraint ensures weight is between 1 and 10.

#### ProjectItemStatus Enum
**File:** `backend/app/models.py`

Python enum defining the lifecycle states:
- `PENDING`: Awaiting optimization
- `SUGGESTED`: Recommended by optimization
- `DECIDED`: Final decision made
- `PROCURED`: Purchase order issued
- `FULFILLED`: Item delivered and invoice submitted
- `PAID`: Payment made
- `CASH_RECEIVED`: Revenue received (for fulfilled requirements)

### 2. Modified Database Models

#### Project Model
**Changes:**
- Added `priority_weight`: Integer (non-nullable, default: 5)
- Added check constraint: priority_weight between 1 and 10
- Added `phases` relationship to ProjectPhase model

#### ProjectItem Model
**Removed Fields:**
- `must_buy_time`: Integer (deprecated time-slot system)
- `allowed_times`: Text (deprecated time-slot system)

**Added Fields:**
- `required_by_date`: Date (non-nullable) - Deadline for item delivery
- `status`: Enum (ProjectItemStatus, non-nullable, default: PENDING)
- `decision_date`: Date (nullable)
- `procurement_date`: Date (nullable)
- `payment_date`: Date (nullable)
- `invoice_submission_date`: Date (nullable)
- `expected_cash_in_date`: Date (nullable)
- `actual_cash_in_date`: Date (nullable)

**Added Relationships:**
- `finalized_decisions`: Relationship to FinalizedDecision model

### 3. Pydantic Schemas Updates

#### New Schemas (`backend/app/schemas.py`)

**ProjectItemStatusEnum:**
- Pydantic enum matching the SQLAlchemy ProjectItemStatus enum

**ProjectPhaseBase, ProjectPhaseCreate, ProjectPhaseUpdate, ProjectPhase:**
- Full CRUD schemas for project phases
- Includes validator to ensure end_date is after start_date

**OptimizationRunBase, OptimizationRunCreate, OptimizationRun:**
- Schemas for optimization run tracking
- Includes status validation pattern

**FinalizedDecisionBase, FinalizedDecisionCreate, FinalizedDecisionUpdate, FinalizedDecision:**
- Complete schemas for decision management
- Links decisions to optimization runs and users

**DecisionFactorWeightBase, DecisionFactorWeightCreate, DecisionFactorWeightUpdate, DecisionFactorWeight:**
- Schemas for managing optimization weights
- Weight validation (1-10 range)

#### Modified Schemas

**ProjectBase, ProjectCreate, ProjectUpdate, Project:**
- Added `priority_weight` field with validation (1-10 range)

**ProjectItemBase, ProjectItemCreate, ProjectItemUpdate, ProjectItem:**
- Removed: `must_buy_time`, `allowed_times` fields
- Added: `required_by_date`, `status`, and all lifecycle date fields
- Removed: time slot validator
- Uses ProjectItemStatusEnum for status field

### 4. Sample Data Updates (`backend/app/seed_data.py`)

#### New Seeding Functions

**create_sample_project_phases():**
- Creates 4 phases per project (Planning, Foundation, Construction, Completion)
- Uses real calendar dates starting from January 1, 2025
- Each project's phases are offset by 90 days

**create_sample_decision_factor_weights():**
- Populates 5 default optimization factors:
  - cost_minimization (weight: 9)
  - lead_time_optimization (weight: 7)
  - supplier_rating (weight: 6)
  - cash_flow_balance (weight: 8)
  - bundle_discount_maximization (weight: 5)

#### Modified Seeding Functions

**create_sample_projects():**
- Added third project (PROJ003)
- All projects now include `priority_weight` values (8, 6, 5)

**create_sample_project_items():**
- Removed old time-slot based fields
- Uses `required_by_date` with real calendar dates
- Includes `status` field (all set to PENDING)
- Creates 6 sample items across 3 projects
- More realistic item names (Steel Beams, Concrete Mix, Rebar)

**seed_sample_data():**
- Updated to call new seeding functions in correct order:
  1. Users
  2. Projects
  3. Assignments
  4. **Project Phases** (new)
  5. Procurement Options
  6. Budget Data
  7. Project Items
  8. **Decision Factor Weights** (new)

## Database Migration Notes

### For New Deployments
The updated models will automatically create the correct schema when the application initializes.

### For Existing Deployments
**IMPORTANT:** This is a breaking change. The following migration strategy is recommended:

1. **Backup existing data** before applying changes
2. **Manual migration required** for:
   - Converting `must_buy_time` and `allowed_times` to `required_by_date`
   - Setting default `status` for existing ProjectItems
   - Assigning default `priority_weight` to existing Projects

3. **Suggested Alembic migration approach:**
   ```python
   # Example migration pseudo-code
   # 1. Add new columns as nullable
   # 2. Populate new columns with converted data
   # 3. Make new columns non-nullable
   # 4. Drop old columns
   ```

4. **Data conversion logic:**
   - Map old time_slot values to actual dates based on project start dates
   - Set all existing items to 'PENDING' status initially
   - Assign default priority_weight of 5 to all projects

## Testing Recommendations

1. **Model Tests:**
   - Verify all new models can be created and persisted
   - Test check constraints (priority_weight, factor weights)
   - Test enum values for ProjectItemStatus

2. **Relationship Tests:**
   - Test cascade deletes work correctly
   - Verify bidirectional relationships

3. **Schema Validation Tests:**
   - Test Pydantic validators (date ranges, enum values)
   - Verify serialization/deserialization

4. **Seed Data Tests:**
   - Run seed_data.py and verify all tables are populated
   - Check for foreign key constraint violations

## Next Steps

### Phase 2: API Endpoints
- Create CRUD endpoints for ProjectPhase
- Create endpoints for FinalizedDecision management
- Add endpoints for DecisionFactorWeight configuration
- Update existing ProjectItem endpoints for new fields

### Phase 3: Optimization Engine
- Refactor optimization_engine.py to use dates instead of time slots
- Incorporate DecisionFactorWeights into optimization logic
- Update to work with new ProjectItem status workflow

### Phase 4: Frontend Updates
- Update UI components to work with calendar dates
- Add phase management interface
- Add decision tracking dashboard
- Update item status workflow UI

## Files Modified

1. `backend/app/models.py` - Core database models
2. `backend/app/schemas.py` - Pydantic validation schemas
3. `backend/app/seed_data.py` - Sample data population
4. `PHASE1_REFACTORING_SUMMARY.md` - This documentation (new)

## Backward Compatibility

**Breaking Changes:**
- ProjectItem model schema is incompatible with previous version
- API endpoints accepting/returning ProjectItem data will need updates
- Optimization engine must be refactored before it can work with new schema

**No Impact:**
- User, Project (other than priority_weight), ProcurementOption models remain compatible
- Authentication system unchanged
- BudgetData model unchanged (time_slot still used for budget periods)

## Additional Notes

- The `BudgetData` model still uses `time_slot` as it represents abstract budget periods rather than project-specific timelines
- The `OptimizationResult` model is kept for backward compatibility but may need future refactoring to align with the new date-based system
- Consider adding indexes on date fields in ProjectItem for performance optimization
- The system now supports multi-project portfolio analysis with weighted priorities

## Questions or Issues?

If you encounter any issues during migration or have questions about the refactoring, please refer to:
- Original requirements in the user query
- SQLAlchemy documentation for model definitions
- Pydantic documentation for schema validation

---

**Refactoring completed:** October 8, 2025
**Next phase:** API endpoint updates and optimization engine refactoring
