# Rivar Restart Audit - API and Frontend Flow Map

## Frontend Flow Map (Procurement-Centric)

## 1) Procurement Workspace

- **File:** `frontend/src/pages/ProcurementPage.tsx`
- **Route:** `/procurement`
- **Purpose:** item-level procurement execution hub with package management
- **Key API calls:**
  - `itemsAPI.listFinalized()`
  - `packagesAPI.listByProjectItem()`, `packagesAPI.get()`, `packagesAPI.delete()`
  - `itemsAPI.listProjectItemSubItems()`, `itemsAPI.get()`
  - `procurementAPI.listByProjectItem()`
  - `deliveryOptionsAPI.listByItem()`
- **Data structures:**
  - finalized project item records
  - package objects with nested `subitems`
  - optional package-linked procurement option metadata
- **Completeness:** high
- **Known gaps:**
  - TODO optimizer preview with package
  - TODO remaining-demand prefill flow refinement

## 2) Project Item Breakdown Authoring

- **File:** `frontend/src/pages/ProjectItemsPage.tsx`
- **Route:** `/projects/:projectId/items`
- **Purpose:** create/edit project items and attach sub-item requirements
- **Key API calls:**
  - `itemsAPI.listByProject/create/update/delete/finalize`
  - `itemsMasterAPI.list/listSubItems/get`
  - `packagesAPI.listByProjectItem()`
- **Data structures:** project items with `sub_items` payload
- **Completeness:** high
- **Known gaps:** no major blocking defect observed in this audit pass

## 3) Package Wizard

- **Files:** `frontend/src/components/PackageWizard/PackageWizard.tsx`, `PackageWizardStep1.tsx`, `PackageWizardStep2.tsx`, `PackageWizardStep3.tsx`
- **Used in:** `ProcurementPage`
- **Purpose:** create/edit package metadata, composition, pricing, delivery/payment terms
- **Key API calls:**
  - `packagesAPI.create/update/createSubItem/deleteSubItem/get/listByProjectItem`
  - `procurementAPI.create` (optional package-linked option)
  - `suppliersAPI.get`
- **Data structures:** wizard model with `subitem_quantities`, payment terms object, optional pricing metadata
- **Completeness:** high
- **Known gaps:** optional procurement-option create can fail silently (warning-only path)

## 4) Package Visibility and Coverage

- **Files:** `frontend/src/components/packages/PackageList.tsx`, `CoverageSummaryModal.tsx`
- **Purpose:** list package rows and coverage analytics per item/project
- **Key API calls:**
  - `packagesAPI.listByProjectItem/get/getCoverageSummary/getProjectCoverageSummary`
  - `procurementAPI.listByProjectItem`
- **Completeness:** medium-high
- **Known gaps:** package optimization preview flow not fully wired

## 5) Feature Flag UI Context

- **File:** `frontend/src/hooks/useFeatureFlags.tsx`
- **Purpose:** load runtime flags and expose package mode
- **Current behavior:** force package mode enabled in frontend regardless of backend values
- **Risk:** can hide backend rollout-state issues

---

## Backend Flow Map (Procurement and Adjacent)

## Package APIs (`backend/app/routers/packages.py`)

- `POST /packages/`
  - **Request schema:** `ProcurementPackageCreate`
  - **Response schema:** `ProcurementPackageResponse`
  - **Models touched:** `ProjectItem`, `ProcurementPackage`
  - **Auth:** authenticated user (`get_current_user`)
- `PUT /packages/{package_id}`, `DELETE /packages/{package_id}`, `GET /packages/{package_id}`
- `GET /packages/by-project-item/{project_item_id}`
- `POST/PUT/DELETE /packages/subitems/*`
  - **Request schemas:** `PackageSubItemCreate`, `PackageSubItemUpdate`
  - **Models touched:** `PackageSubItem`, `ProjectItemSubItem`
- `GET /packages/coverage/{project_item_id}`
  - **Service:** `calculate_coverage_summary`

## Project Item APIs (`backend/app/routers/items.py`)

- `GET /items/project/{project_id}`
- `POST /items/`, `PUT /items/{item_id}`, `DELETE /items/{item_id}`
- `GET /items/{item_id}/subitems`
- `PUT /items/{item_id}/finalize`, `PUT /items/{item_id}/unfinalize`
- **Model touchpoints:** `ProjectItem`, `ProjectItemSubItem`
- **Auth:** authenticated user

## Procurement Option APIs (`backend/app/routers/procurement.py`)

- `GET /procurement/options`, `/procurement/options/{item_code}`, `/procurement/options/by-project-item/{project_item_id}`
- `POST /procurement/options`, `PUT /procurement/option/{id}`, `DELETE /procurement/option/{id}`
- **Schemas:** `ProcurementOptionCreate/Update` path through CRUD
- **Model touchpoints:** `ProcurementOption`, `Supplier`, optional `ProcurementPackage`
- **Validation chain:** package/legacy reference + supplier reference validators

## Delivery Option APIs (`backend/app/routers/delivery_options.py`)

- CRUD endpoints under `/delivery-options`
- supports package-aware references in create/update flows
- **Model touchpoints:** `DeliveryOption`, optional package linkage

## Decision APIs (`backend/app/routers/decisions.py`)

- List/count/summary and save endpoints
- `POST /decisions/proposals` (save optimized proposal as decisions)
- package resolution integration via `get_package_for_project_item`
- **Model touchpoints:** `FinalizedDecision`, `CashflowEvent`, `ProcurementOption`

## Project Coverage/Package APIs (`backend/app/routers/projects.py`)

- `GET /projects/{project_id}/packages`
- `GET /projects/{project_id}/coverage-summary`
- **Service:** package coverage aggregation

## Finance and Optimization APIs (`backend/app/routers/finance.py`)

- Budget CRUD: `/finance/budget*`
- Optimization: `/finance/optimize`, `/finance/optimize-enhanced`
- Run/result management and cleanup endpoints

---

## Auth and Role Enforcement

- Most procurement-relevant routes require authentication via `get_current_user`.
- Role helper methods exist in `backend/app/auth.py`, but many endpoints do not apply strict role dependencies in decorator signatures.

## Test Mapping

- **CRUD/validator/audit coverage:** present in `backend/tests/test_crud_phase3.py`, `test_validators.py`, `test_audit_service.py`
- **API integration coverage:** `backend/tests/test_api_phase3.py` currently placeholder/skipped
