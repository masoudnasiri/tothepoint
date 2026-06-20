# Rivar Phase 8 Demo Script

This script is for business demos (non-developer audience).  
It assumes demo data has already been created with:

`python scripts/create_demo_dataset.py --mode create`

All demo records are tagged with `DEMO_RC8_`.

## 1) Login

1. Open the product URL.
2. Login with a business demo user (admin/procurement/finance/PM as needed).
3. Confirm the dashboard opens successfully.

## 2) Open Dashboard

1. Go to `Dashboard`.
2. Explain high-level KPIs and that values include demo data tagged `DEMO_RC8_`.

## 3) Show Projects

1. Go to `Projects`.
2. Find and open:
   - `DEMO_RC8_PRJ_DC` (data-center style project)
   - `DEMO_RC8_PRJ_SEC` (monitoring/security style project)

## 4) Show Project Item and Sub-item Breakdown

1. Open `DEMO_RC8_PRJ_DC` items.
2. Open item `DEMO_RC8_ITEM_SERVER`.
3. Show that `Server` is decomposed into:
   - Case
   - CPU
   - Heatsink
   - RAM
   - Storage
   - Power Supply
   - Rail Kit
   - Network Card

## 5) Show Supplier Packages

1. Go to `Procurement` for `DEMO_RC8_ITEM_SERVER`.
2. Show packages:
   - `DEMO_RC8_PKG_SERVER_INCOMPLETE` (partial/incomplete)
   - `DEMO_RC8_PKG_SERVER_PART_A`
   - `DEMO_RC8_PKG_SERVER_PART_B`
   - `DEMO_RC8_PKG_SERVER_FULL`
3. Explain supplier/payment-term differences:
   - one full package supplier
   - two complementary partial suppliers
   - different payment terms in procurement options

## 6) Show Package Coverage

1. Open coverage summary for `DEMO_RC8_ITEM_SERVER`.
2. Show that incomplete package does not cover all required sub-items/quantities.
3. Show that full package provides full coverage.

## 7) Demonstrate Incomplete Coverage Lock Rejection

1. Open `Decisions`.
2. Locate decision `incomplete_lock_should_fail` from dataset output (or tagged `DEMO_RC8_` note).
3. Attempt to lock/finalize decision.
4. Show expected rejection message for incomplete coverage.

## 8) Demonstrate Complete Coverage Lock Success

1. Locate decision `complete_lock_should_pass` from dataset output.
2. Lock/finalize decision.
3. Show success state (`LOCKED`).

## 9) Show Procurement Plan

1. Go to `Procurement Plan`.
2. Confirm locked demo decisions appear.
3. Highlight package/supplier context for traceability.

## 10) Confirm Delivery (Procurement Role)

1. On a locked demo decision, use `confirm delivery`.
2. Enter demo delivery data and save.
3. Show status update.

## 11) Accept Delivery as PM

1. Switch/login as PM role.
2. Accept delivery for the same decision.
3. Confirm lifecycle status moves correctly.

## 12) Enter Invoice / Payment-In

1. Go to finance invoice/payment flow.
2. Enter invoice for locked demo decision.
3. Enter customer payment-in.
4. Confirm data saved.

## 13) Enter Supplier Payment

1. Open supplier payments.
2. Enter supplier payment-out for the same decision.
3. Confirm record appears and links to decision/package/supplier context.

## 14) Show Cashflow / Reports / Dashboard Impact

1. Open `Dashboard`, `Reports`, or `Analytics`.
2. Show inflow/outflow visibility from demo finance actions.
3. Explain that these are linked to decision lifecycle.

## 15) Show Audit Log Traceability

1. Open `Audit Logs`.
2. Filter with `DEMO_RC8_` or lifecycle action names.
3. Show that decision/finance operations are traceable.

## Demo Cleanup (Optional)

To remove demo rows after the demo:

`python scripts/create_demo_dataset.py --mode cleanup`
