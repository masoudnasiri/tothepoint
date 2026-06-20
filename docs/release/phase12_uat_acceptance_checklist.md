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

## وضعیت نهایی پذیرش

- [ ] No blocker
- [ ] No unresolved major without workaround
- [ ] UAT accepted by business owner

