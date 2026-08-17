# 32 — IT Procurement Demo Dataset for 1405

## Scenario

Deterministic IT procurement portfolio for Jalali year 1405. The dataset follows the live Rivar workflow:

1. Master/base items
2. Sub-items/components
3. Suppliers
4. Projects
5. Project items
6. Project item sub-items
7. Delivery/sales options
8. Finalization of eligible items
9. Procurement expert assignment
10. Packages and supplier options
11. Budget periods with one shortage window
12. Optimization readiness without locking final decisions

Prefix: `DEMO_IT_1405_`

Existing non-demo rows were not deleted. `docker compose down -v` was not used. The database was not reset.

## Date range

- Jalali: 1 Shahrivar 1405 to 29 Esfand 1405 (`1405-06-01` to `1405-12-29`)
- Gregorian stored in DB: `2026-08-23` to `2027-03-20`
- Conversion is hardcoded in the seed script. The application stores Gregorian dates.

Jalali month starts used for budget periods:

| Jalali month | Gregorian budget date |
| --- | --- |
| Shahrivar 1405 | 2026-08-23 |
| Mehr 1405 | 2026-09-23 |
| Aban 1405 | 2026-10-23 |
| Azar 1405 | 2026-11-22 |
| Dey 1405 | 2026-12-22 |
| Bahman 1405 | 2027-01-21 |
| Esfand 1405 | 2027-02-20 |

## Currency / unit convention

All stored amounts are Iranian Rial (`IRR`).

- 1 Toman = 10 Rial
- Example: laptop sales `450,000,000` IRR = `45,000,000` Toman

Prices are demo assumptions for presentation, not official supplier quotes. The script contains a pricing assumptions table. FX-sensitive options use a documented assumption of `850,000` IRR per USD.

## Master item categories

26 master items, 131 sub-items. 21 of 26 masters (81%) have components.

- Server Equipment: Rack Server, GPU Server, Storage Server, Tower Server
- Network Equipment: Core Switch, Access Switch, Router, Firewall, Wireless AP, SFP Module, Patch Panel
- Storage and Backup: NAS, SAN, Backup Appliance, Tape Backup
- Security and Monitoring: CCTV NVR, IP Camera, Access Control, Security Sensor, SIEM
- End-User and Office IT: Business Laptop, Engineering Workstation, Mini PC, Monitor, Docking Station, UPS

Simple items without decomposition: SFP Module, Patch Panel, Security Sensor, Monitor, Docking Station.

## Suppliers and differentiators

12 suppliers were created. Assignments rotate between existing procurement users `proc1` and `proc2`.

| Code | Name | Positioning | Strength | Weakness |
| --- | --- | --- | --- | --- |
| SUP01 | DEMO_IT_1405_پردازش‌گران آتیه | server/storage specialist | enterprise hardware | longer delivery |
| SUP02 | DEMO_IT_1405_شبکه‌افزار سپهر | network specialist | switches/routers/firewalls | license lead time |
| SUP03 | DEMO_IT_1405_داده‌پردازان رسا | general IT | competitive price | limited warranty |
| SUP04 | DEMO_IT_1405_ایمن‌سازان هوشمند | security/monitoring | CCTV/access control | partial stock |
| SUP05 | DEMO_IT_1405_رایان‌گستر خاورمیانه | laptops/office IT | fast delivery | higher price |
| SUP06 | DEMO_IT_1405_فناوران ابری کوشا | virtualization/cloud | license/implementation bundle | higher service cost |
| SUP07 | DEMO_IT_1405_نوآوران ذخیره‌سازی | storage/backup | SAN/NAS/backup | FX-sensitive pricing |
| SUP08 | DEMO_IT_1405_راهکارهای مرکز داده کارا | datacenter packages | complete bundles | stricter payment |
| SUP09 | DEMO_IT_1405_ارتباطات امن پارسیان | firewall/VPN | security support | license dependency |
| SUP10 | DEMO_IT_1405_سامانه‌پرداز نگین | mixed IT | flexible payment | medium delivery reliability |
| SUP11 | DEMO_IT_1405_تجهیزات رایان مهر | endpoint/accessories | low price | limited enterprise warranty |
| SUP12 | DEMO_IT_1405_زیرساخت هوشمند آریا | project infrastructure | balanced terms | limited specialized stock |

## Project and procurement counts

| Metric | Result |
| --- | --- |
| Projects | 30 |
| Project items | 900 |
| Finalized / sent to procurement | 270 (30%) |
| Procurement assignments | 270 |
| Items with supplier options | 216 (80% of finalized) |
| Supplier options | 648 |
| Packages | 648 |
| Package sub-item rows | 3401 |
| Budget records | 7 |
| Shortage window | Mehr 1405 (`2026-09-23`), yes |
| Optimization-ready items | 216 |
| Optimization submissions (`SENT`, not locked) | 108 |

Project names match the requested IT portfolio (Data Center Modernization through Enterprise Reporting Infrastructure). Item counts per project sum to exactly 900.

## Package / sub-item coverage

Decomposed finalized items received:

- full packages covering all required sub-items
- complementary partial packages (first half / second half)
- intentional incomplete packages (`partial_stock`) for optimization coverage demos

Simple items received full packages only.

## Budget

Normal months: `500,000,000,000` IRR  
Shortage month (Mehr 1405): `80,000,000,000` IRR

If a `budget_data` row already exists for a period, the script increments it and stores the original value in an audit snapshot so cleanup can restore it. On this run the seven period dates were created by the demo.

## Why ORM inserts were used

There is no bulk seed API. Creating ~900 items and ~600 options over HTTP would still write the same tables. The script uses the live SQLAlchemy models and the same fields used by finalization, assignment, package, and procurement-option services.

A sample of 12 options was passed through `apply_procurement_option_persistence_contract`.

## Commands

From the compose project directory (`/root/pdss` on the live server):

```bash
docker compose run --rm -e PYTHONPATH=/app backend python scripts/create_it_procurement_demo_1405.py --mode create
docker compose run --rm -e PYTHONPATH=/app backend python scripts/create_it_procurement_demo_1405.py --mode cleanup
docker compose run --rm -e PYTHONPATH=/app backend python scripts/create_it_procurement_demo_1405.py --mode verify
```

`create` cleans only `DEMO_IT_1405_` rows first, then recreates the dataset. If a previous create left a partial prefix set, run `cleanup` in a separate process, then:

```bash
docker compose exec -T -e PYTHONPATH=/app backend python scripts/create_it_procurement_demo_1405.py --mode create --skip-pre-clean
```

## Verification output

Create/verify summary after the successful feed:

- master items: 26
- sub-items: 131
- suppliers: 12
- projects: 30
- project items: 900
- finalized: 270
- assignments: 270
- items with options: 216
- supplier options: 648
- packages: 648
- package sub-items: 3401
- budget records: 7
- shortage window: Mehr 1405
- optimization-ready: 216
- no `DEMO_RC8_` dependency
- no `PH5` dependency

Cleanup verification: after `--mode cleanup`, verify reported zeros for all demo counts. The dataset was then recreated and left in place for presentation.

## Runtime page/API load

| Check | Result |
| --- | --- |
| `docker compose ps` | backend/frontend/postgres healthy |
| `GET /health` | 200 |
| admin login | 200 |
| `GET /dashboard/summary` | 200 |
| `GET /projects` | 200 |
| `GET /procurement/items-with-details` | 200 |
| `GET /procurement/options` | 200 after payment-terms/currency fix |
| `GET /procurement-assignments/assigned-items` | 200 |
| `GET /finance/optimization-runs` | 200 (empty runs, as designed) |
| Frontend `/` | 200 |
| Frontend `/dashboard`, `/procurement`, `/optimization-enhanced` | HTTP 404 on deep link (SPA has no server fallback). App shell at `/` loads. |

## Tests and build

- Backend `pytest tests -q`: collection error in pre-existing `tests/test_phase13f_financial_projection_engine.py` (`ImportError: cannot import name 'financial_projections'`). Not introduced by this demo feed.
- Frontend `npm run build`: passed with existing ESLint unused-variable warnings.

## Schema note

The live `procurement_options` table was missing later contract columns (`payment_method_id`, delivery/forecast dates). An additive `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` was applied. No tables were dropped and no existing rows were deleted by that change.

## Known limitations

- Prices are demo assumptions, not live market quotes.
- Direct ORM writes were used because no bulk seed API exists.
- `create` plus a large in-process cleanup can drop the Postgres connection on this host. Prefer cleanup, then create with `--skip-pre-clean` if that happens.
- Frontend deep links return 404 at nginx/static level; this predates the demo feed.
- Decisions were not locked. Optimization submissions mark readiness only.
- IRR currency row is created if missing and is not removed by cleanup.

## Remaining risks / next action

1. Fix the Phase 13F `financial_projections` import so the full backend suite can collect.
2. Add SPA fallback for `/dashboard`, `/procurement`, and `/optimization-enhanced`.
3. Use this dataset for an optimization demo around Mehr 1405 shortage pressure.
