# چک‌لیست پذیرش UAT - فاز ۱۲ (پس از بازطراحی)

## هویت و ورود

- [ ] Login works
- [ ] `Rivar / Corbit / 1.0.0-rc1` visible
- [ ] RTL/Persian UI acceptable

## فهم‌پذیری UI و داشبورد

- [ ] Dashboard understandable
- [ ] Projects visible
- [ ] Project items visible
- [ ] Sub-items visible
- [ ] Budget is shown as budget/capacity (not customer inflow)
- [ ] Before optimization/decision lock: forecast inflow/outflow remain zero (unless committed schedules exist)
- [ ] Before finance events: actual inflow/outflow remain zero
- [ ] Pre-decision project sales and unselected procurement options are excluded from forecast/actual

## صحت دیتاست

- [ ] 100 master items exist
- [ ] 10 projects exist
- [ ] About 500 project items exist
- [ ] 40 approved suppliers exist
- [ ] Currencies exist (IRR, USD, EUR, AED, CNY, TRY)
- [ ] Monthly budgets exist from Tir to Esfand 1405
- [ ] 70% finalized/sent-to-procurement ratio verified
- [ ] About 70% of finalized items have procurement data
- [ ] Delivery mismatch distribution visible (early/aligned/late)
- [ ] Package coverage states visible (full/partial/missing)

## قابلیت استفاده جریان‌های کلیدی

- [ ] Finance budget screen usable
- [ ] Procurement flow usable
- [ ] Optimization can be run by user
- [ ] Decisions can be reviewed by user
- [ ] Reports/dashboard/audit reflect user actions

## چک‌لیست اختصاصی فاز 12C

- [ ] Package Wizard finalization flag persists and package status shows `Finalized`
- [ ] Draft/non-finalized package cannot be sent to optimization
- [ ] Full-coverage partial-package combinations are generated and selectable
- [ ] Incomplete coverage requires explicit confirmation before submission
- [ ] Bulk send (`Send all finalized packages to optimization`) respects confirmation and skip behavior
- [ ] Sent item is locked for package create/edit/delete (backend + UI)
- [ ] Safe rollback re-enables editing only when no blocking decisions exist
- [ ] Optimization state filter works (`all/not sent/sent/rolled back`)
- [ ] Coverage state filter works (`all/no package/partial/full/over-covered/missing components`)
- [ ] Coverage labels distinguish current package vs aggregate vs optimization-eligible semantics

## چک‌لیست اختصاصی فاز 12D

- [ ] Bulk rollback button (`Rollback from optimization`) is visible for sent items
- [ ] Rollback preview dialog supports checklist filters (package type, coverage state, supplier type, single/multiple supplier, warning-confirmed incomplete)
- [ ] IRR price range filter (min/max) affects preview as expected
- [ ] Date range filter with selectable date field affects preview as expected
- [ ] Preview shows matched/rollbackable/unsafe counts and unsafe skip reasons
- [ ] Execute endpoint rejects rollback when confirmation flag is false
- [ ] Unsafe items are skipped (not silently rolled back) with explicit reason payload
- [ ] Safe selected items rollback successfully and item state changes out of `sent_to_optimization`
- [ ] Package create/edit/delete actions become available again after rollback
- [ ] Bulk rollback audit events are present (success/skip/summary)

## چک‌لیست اختصاصی فاز 12E-0

- [ ] Pre-run optimization budget analysis is scenario-based (`minimum`, `average`, `conservative`, `selected result`)
- [ ] Scenario semantics confirm each item is counted once (alternative candidates/combos are not cumulatively summed)
- [ ] Budget shortage is shown as warning decision point (not hard blocker)
- [ ] Warning dialog shows 3 actions (constrained / allow-shortage / cancel)
- [ ] `constrained` mode returns budget-fitting subset and reports deferred/excluded items
- [ ] `allow_shortage` mode runs and returns shortage analysis
- [ ] Proposal/result-level financial analysis is accessible and coherent
- [ ] Currency display uses correct symbols/labels for IRR/USD/EUR/AED/CNY/TRY

## چک‌لیست اختصاصی فاز 12E-1

- [ ] Both execution modes are testable (`constrained` and `allow_shortage`)
- [ ] `allow_shortage` mode does not fail because of budget shortage alone
- [ ] On failure, diagnostics identify non-budget root cause (not generic message)
- [ ] Response includes machine-readable `error_code` and structured `diagnostics`
- [ ] Partial feasible behavior works when only subset of items has valid candidates
- [ ] Skipped/infeasible item reasons are visible
- [ ] Budget-filtered count is visible in constrained runs

## چک‌لیست اختصاصی فاز 12E-2

- [ ] Changing scenario updates all report sections, not only header text
- [ ] `minimum_feasible` vs `average_candidate` vs `worst_case` show different totals where data supports it
- [ ] Cards/charts/period detail/narrative are consistent with the same selected scenario
- [ ] No legacy/default analysis leakage after scenario change
- [ ] `selected_optimization_result` analysis uses selected candidates from that run only
- [ ] Selected-result narrative includes `تحلیل مالی مدل انتخابی`
- [ ] Required budget is numerically consistent across header/cards/charts/period totals
- [ ] Persian UI keeps Jalali period labels consistently in budget-analysis visuals

## وضعیت نهایی پذیرش

- [ ] No blocker
- [ ] No unresolved major without workaround
- [ ] UAT accepted by business owner

