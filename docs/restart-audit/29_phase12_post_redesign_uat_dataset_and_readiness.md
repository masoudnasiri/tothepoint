# 29) Phase 12 - Post-Redesign UAT Dataset and Readiness

## Environment Target

- Target path: `/root/pdss_demo`
- Compose project: `pdss_demo`
- Public ports in use:
  - Backend: `18010`
  - Frontend: `13010`
  - Postgres: `15440`
- Production guard check:
  - Production stack `/root/pdss` exists separately on ports `8000/3000/5432`
  - Destructive operations were executed **only** on `/root/pdss_demo`

## Backup Result

- Backup taken before destructive reset:
  - `/root/pdss_backups/pdss_demo_pre_phase12_20260620_151515.sql`
- Backup file size validated (`test -s` + `ls -lh`)
- Result: **PASS**

## Reset Result (Domain Data Only)

- Reset mode used: `python scripts/create_uat_1405_dataset.py --mode reset-domain-data`
- Domain tables cleaned in FK-safe order (procurement options before delivery options, etc.)
- Users preserved:
  - before: `8`
  - after: `8`
  - preserved flag: `true`
- Roles/auth records: preserved (user table untouched)
- Result: **PASS**

## Data Creation Method

- Generator file: `backend/scripts/create_uat_1405_dataset.py`
- Mode used for end-to-end creation: `--mode reset-and-create`
- Creation path:
  - Backend CRUD/services/schemas used (`create_project_item`, `create_procurement_option`, `create_delivery_option`, package coverage validators)
  - ORM used for controlled cleanup/reset and controlled seed creation
  - No ad-hoc raw SQL inserts for dataset creation
- Jalali conversion method:
  - Deterministic Jalaali algorithm utility in script
  - Range: Tir 1405 -> Esfand 1405 (Gregorian mapped in validate output)

## Dataset Counts

- Master items: `100`
- Sub-items: `497`
- Projects: `10`
- Project items: `500`
- Finalized / sent-to-procurement: `350`
- Non-finalized: `150`
- Suppliers:
  - Domestic: `20`
  - Foreign: `20`
  - Approved active: `40`
- Currencies: `IRR, USD, EUR, AED, CNY, TRY`
- Budget months created: `9` (Tir to Esfand 1405)
- Procurement records:
  - Items with procurement data: `245`
  - Packages: `327`
  - Procurement options: `327`

## Coverage and Delivery Summary

- Coverage state summary:
  - Fully covered: `164`
  - Partially covered: `81`
  - Uncovered: `0`
- Delivery mismatch summary:
  - Early: `61`
  - Aligned: `123`
  - Late: `61`

## Optimization Confirmation

- Optimization run in dataset preparation: **NO**
- Finalized decision rows present: `0`
- Dataset is prepared for manual user-driven optimization/decision review.

## Quality Gates

- `docker compose ps` (demo stack): **PASS**
- `curl http://127.0.0.1:18010/health`: **PASS**
- Login check (`admin/admin123`): **PASS**
- `docker compose run --rm backend python -m pytest tests -q`: **PASS** (`39 passed, 4 skipped`)
- `docker compose run --rm backend python -m pytest tests/test_phase8_release_candidate_smoke.py -q`: **PASS** (`3 passed`)
- `docker compose run --rm frontend npm run build`: **PASS** (with pre-existing lint warnings)
- `python scripts/create_uat_1405_dataset.py --mode validate`: **PASS**

## Known Limitations

- Existing frontend lint warnings are present in the redesign workstream; build still succeeds.
- Coverage has no fully zero-covered procurement item in current seed; missing sub-item scenarios are represented through partially covered records.
- Supplier/document file uploads are not pre-seeded in this dataset.

## Artifacts

- Dataset summary JSON: `docs/release/phase12_uat_dataset_summary.json`
- UAT guide: `docs/release/phase12_business_user_uat_guide.md`
- Issue template: `docs/release/phase12_uat_issue_template.md`
- Acceptance checklist: `docs/release/phase12_uat_acceptance_checklist.md`

## Phase 12 Status

- **closed**

