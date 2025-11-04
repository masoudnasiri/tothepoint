# Budget Analysis - Item Tracking for CUSCO-ROUTER-KJDHKJDBHFKJG

## How Budget Analysis Works

The budget analysis considers items in **two categories**:

### 1. **Finalized Decisions** (Committed Procurements)
- Items that have a `FinalizedDecision` record with status `LOCKED` or `PROPOSED`
- These represent **actual commitments** that have been made
- Cash flows are calculated based on:
  - Actual payment installments (if entered by finance team)
  - Payment terms from procurement options
  - Actual or forecast invoice dates and amounts

### 2. **Pending Project Items** (Forecast Needs)
- Project items that do NOT have a finalized decision yet
- These represent **planned procurements** that need budget allocation
- Cash flows are estimated using:
  - **Finalized procurement options** (if available) - uses MAXIMUM price for conservative budgeting
  - Active procurement options (if no finalized options exist) - uses MAXIMUM price
  - Delivery options to estimate invoice timing and amounts

## How CUSCO-ROUTER-KJDHKJDBHFKJG is Processed

### Scenario A: Item has NO Finalized Decision
- ✅ **Included** in "Pending Project Items"
- ✅ Uses the finalized procurement option ($2,000 USD) for budget estimation
- ✅ Calculates outflow based on delivery date from delivery option
- ✅ Calculates inflow based on invoice timing from delivery option
- ✅ Preserves USD currency throughout

### Scenario B: Item HAS a Finalized Decision
- ✅ **Excluded** from "Pending Project Items" 
- ✅ **Included** in "Finalized Decisions"
- ✅ Uses actual payment schedule from finalized decision
- ✅ Uses actual or forecast invoice data from finalized decision
- ✅ Preserves USD currency throughout

## Verification Steps

After running budget analysis, check backend logs for:

1. **Item Loading:**
   ```
   Item CUSCO-ROUTER-KJDHKJDBHFKJG (Project X): decided=<true/false>, included=<true/false>
   ```

2. **If in Pending Items:**
   ```
   Item CUSCO-ROUTER-KJDHKJDBHFKJG: X finalized options, Y total options
     Option Z: finalized=True, currency=USD, cost=2000
   Item CUSCO-ROUTER-KJDHKJDBHFKJG - Using MAXIMUM price from X finalized options: 2000 USD
   ```

3. **If in Finalized Decisions:**
   ```
   Found finalized decision for CUSCO-ROUTER-KJDHKJDBHFKJG: status=LOCKED, cost=2000 USD
   ```

4. **Check the API Response:**
   - Look for `periods` array with entries showing `USD` currency
   - Check `total_needed_by_currency` for `"USD"` key
   - Verify amounts match expected values

## Currency Preservation

The analysis now:
- ✅ Preserves original currency (USD) for all calculations
- ✅ Shows separate currency cards in frontend
- ✅ Tracks gaps per currency independently

## Troubleshooting

If the item is NOT appearing:

1. **Check if it has a finalized decision:**
   - If YES → Should appear in finalized decisions cash flows
   - If NO → Should appear in pending items forecast

2. **Check procurement options:**
   - Ensure at least one procurement option exists for the item_code
   - Verify the option has `is_finalized=True` or `is_active=True`
   - Verify `cost_currency` is set to "USD"

3. **Check item_code matching:**
   - Ensure exact match (case-sensitive, no extra spaces)
   - The system normalizes by trimming whitespace

4. **Check date filters:**
   - If date range is specified, ensure delivery/purchase dates fall within range

