# Your First Optimization Run - Step-by-Step Guide

## 🎯 Goal
Successfully run your first enhanced optimization and understand the results.

---

## ✅ Prerequisites Checklist

Before starting, ensure you have:

- [ ] Backend server running (`uvicorn app.main:app --reload`)
- [ ] Frontend server running (`npm start`)
- [ ] Logged in as **admin** or **finance** user
- [ ] Test data loaded:
  - [ ] At least 1 active project
  - [ ] At least 5 project items with delivery options
  - [ ] At least 5 procurement options
  - [ ] At least 3 budget periods

**Don't have test data?** See [Adding Test Data](#adding-test-data) section below.

---

## 📋 Step-by-Step Instructions

### Step 1: Navigate to Advanced Optimization

1. **Open your browser** to `http://localhost:3000`

2. **Login** with your credentials:
   - Username: `admin` (or your finance user)
   - Password: [your password]

3. **Click** "Advanced Optimization" in the sidebar menu
   - Icon: 🧠 (Psychology/brain icon)
   - Should be between "Optimization" and "Finalized Decisions"

4. **Verify page loaded**:
   - Should see 4 solver cards (CP_SAT, GLOP, SCIP, CBC)
   - Should see "Run Optimization" button
   - Page title: "Advanced Optimization"

---

### Step 2: Understand the Solver Cards

You should see 4 cards:

```
┌─────────────────┐  ┌─────────────────┐
│    CP_SAT       │  │      GLOP       │
│ ✅ Selected     │  │   Available     │
└─────────────────┘  └─────────────────┘

┌─────────────────┐  ┌─────────────────┐
│     SCIP        │  │      CBC        │
│   Available     │  │   Available     │
└─────────────────┘  └─────────────────┘
```

**For your first run:**
- ✅ Keep **CP_SAT** selected (it's selected by default)
- ℹ️ Click the info icon (ⓘ) on any card to learn more

**Why CP_SAT for first run?**
- Most flexible solver
- Handles all types of constraints
- Provides true optimal solutions
- Good for learning what's possible

---

### Step 3: Configure Your First Run

1. **Click** the "Run Optimization" button

2. **In the dialog that opens**, you'll see:

```
┌────────────────────────────────────────────┐
│  Configure Advanced Optimization           │
├────────────────────────────────────────────┤
│                                            │
│  Solver Type: [CP_SAT ▼]                  │
│                                            │
│  Maximum Time Slots: [12]                 │
│  (Number of time periods to consider)      │
│                                            │
│  Time Limit (seconds): [300]              │
│  (Maximum optimization time)               │
│                                            │
│  ☑ Generate Multiple Proposals            │
│                                            │
│  Strategies (leave empty for all):         │
│  [                               ]         │
│                                            │
│  [Cancel]              [Run Optimization]  │
└────────────────────────────────────────────┘
```

3. **Recommended Settings for First Run:**

   **Solver Type:** `CP_SAT` ✅ (default)
   
   **Maximum Time Slots:** `12` ✅ (default)
   - This means you're optimizing across 12 time periods
   - Each period typically represents a month
   - Adjust based on your planning horizon
   
   **Time Limit (seconds):** `120` ⚠️ **CHANGE THIS**
   - Default is 300 seconds (5 minutes)
   - For first run, set to **120** (2 minutes) for faster results
   - You can increase later for better solutions
   
   **Generate Multiple Proposals:** ✅ **ENABLED**
   - This will generate 5 different proposals (one per strategy)
   - You can compare them side-by-side
   - Highly recommended for first run!
   
   **Strategies:** ⬜ **LEAVE EMPTY**
   - Empty = all strategies will be generated
   - You'll get 5 proposals to compare

4. **Your configuration should look like:**
   ```
   Solver Type: CP_SAT
   Maximum Time Slots: 12
   Time Limit: 120 seconds
   Generate Multiple Proposals: ✅ Enabled
   Strategies: (empty)
   ```

5. **Click** "Run Optimization"

---

### Step 4: Wait for Results

You'll see a progress indicator:

```
┌────────────────────────────────────────────┐
│  🔄 Running Optimization...                │
├────────────────────────────────────────────┤
│  Using CP_SAT solver with multiple         │
│  strategies. This may take several         │
│  minutes.                                   │
│                                            │
│  [████████████░░░░░░░░░] 60%              │
└────────────────────────────────────────────┘
```

**What's happening behind the scenes:**
1. Loading your projects and items from database
2. Building dependency graph
3. Running optimization for each strategy:
   - Strategy 1: LOWEST_COST
   - Strategy 2: PRIORITY_WEIGHTED
   - Strategy 3: FAST_DELIVERY
   - Strategy 4: SMOOTH_CASHFLOW
   - Strategy 5: BALANCED
4. Extracting and formatting results

**Expected wait time:**
- 5 items: ~30 seconds
- 20 items: ~1-2 minutes
- 50 items: ~2-3 minutes
- 100 items: May reach time limit (that's OK!)

**Don't worry if:**
- It says "FEASIBLE" instead of "OPTIMAL"
- Not all strategies complete
- Time limit is reached

All of these are normal for first runs!

---

### Step 5: Review Your Results

Once complete, you should see:

#### **Success Banner**
```
✅ Optimization completed! Generated 5 proposal(s).
   Best cost: $[amount]
```

#### **Summary Statistics**
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│   Status     │ Best Cost    │  Proposals   │ Execution    │
│   OPTIMAL    │  $125,000    │      5       │   89.2s      │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

#### **Proposal Tabs**
```
┌─────────────────────────────────────────────────────────────┐
│ [💰 Lowest Cost] [🎯 Priority] [⚡ Fast] [📊 Flow] [⚖️ Balanced] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Lowest Cost Strategy                                       │
│  CP-SAT solver: 25 items optimized                         │
│                                                             │
│  ┌─────────────┬─────────────┐                            │
│  │ Total Cost  │ Weighted    │                            │
│  │ $125,000    │ $875,000    │                            │
│  └─────────────┴─────────────┘                            │
│                                                             │
│  [Decisions Table]                                          │
│  ...                                                        │
└─────────────────────────────────────────────────────────────┘
```

---

### Step 6: Understand Each Proposal

Click through each proposal tab to understand the differences:

#### **1. Lowest Cost Strategy 💰**
```
Goal: Minimize total spending
Ignores: Project priorities, delivery time
Best for: Budget-constrained scenarios

Example:
- Total Cost: $125,000 (lowest!)
- Items: 25
- Average Delivery: Period 8 (later)
```

#### **2. Priority-Weighted Strategy 🎯**
```
Goal: Prioritize important projects
Considers: Project priority weights
Best for: Portfolio optimization

Example:
- Total Cost: $128,000 (slightly higher)
- Items: 25
- High-priority projects get earlier/better options
```

#### **3. Fast Delivery Strategy ⚡**
```
Goal: Get items delivered ASAP
Ignores: Cost (within budget)
Best for: Time-critical projects

Example:
- Total Cost: $135,000 (highest)
- Items: 25
- Average Delivery: Period 4 (earliest!)
```

#### **4. Smooth Cash Flow Strategy 📊**
```
Goal: Distribute spending evenly
Avoids: Spending spikes
Best for: Cash flow management

Example:
- Total Cost: $127,000
- Items: 25
- Even distribution across periods
```

#### **5. Balanced Strategy ⚖️**
```
Goal: Balance all factors
Considers: Cost, priority, time
Best for: General use

Example:
- Total Cost: $126,500
- Items: 25
- Good balance of all factors
```

---

### Step 7: Analyze a Proposal in Detail

**Click on any proposal tab**, then scroll down to see the **Decisions Table**:

```
┌──────────┬────────┬──────────┬──────────┬──────────┬────────┬──────────┬──────────┬─────────┐
│ Project  │ Item   │ Supplier │ Purchase │ Delivery │ Qty    │ Unit     │ Total    │ Payment │
│          │        │          │ Date     │ Date     │        │ Cost     │ Cost     │         │
├──────────┼────────┼──────────┼──────────┼──────────┼────────┼──────────┼──────────┼─────────┤
│ PROJ-001 │ ITEM-1 │ Acme Co  │ 2025-11  │ 2025-12  │ 100    │ $50.00   │ $5,000   │ Cash    │
│ PROJ-001 │ ITEM-2 │ Beta Inc │ 2025-11  │ 2026-01  │ 50     │ $120.00  │ $6,000   │ Install │
│ PROJ-002 │ ITEM-3 │ Gamma    │ 2025-12  │ 2026-01  │ 200    │ $75.00   │ $15,000  │ Cash    │
│ ...      │ ...    │ ...      │ ...      │ ...      │ ...    │ ...      │ ...      │ ...     │
└──────────┴────────┴──────────┴──────────┴──────────┴────────┴──────────┴──────────┴─────────┘
```

**What to look for:**

1. **Purchase vs. Delivery Dates:**
   - Purchase Date = When you place the order
   - Delivery Date = When item arrives
   - Gap = Lead time

2. **Unit Cost:**
   - May include discounts (cash discount, bundling)
   - Compare across proposals

3. **Payment Terms:**
   - `Cash` = Pay immediately (usually discounted)
   - `Installments` = Pay over time

4. **Quantity:**
   - Should match your project requirements
   - Check for bundling (e.g., quantities rounded up)

---

### Step 8: Compare Proposals

**Create a comparison table:**

| Metric | Lowest Cost | Priority | Fast Delivery | Smooth Flow | Balanced |
|--------|------------|----------|---------------|-------------|----------|
| Total Cost | $125,000 ✅ | $128,000 | $135,000 | $127,000 | $126,500 |
| Avg Delivery | Period 8 | Period 7 | Period 4 ✅ | Period 6 | Period 6 |
| Cash Flow Variance | High | Medium | High | Low ✅ | Medium |
| Priority Score | Medium | High ✅ | Low | Medium | High |

**Ask yourself:**

1. **What's most important to me?**
   - Pure cost savings? → Choose Lowest Cost
   - Fast delivery? → Choose Fast Delivery
   - Smooth cash flow? → Choose Smooth Flow
   - Balance? → Choose Balanced

2. **Can I afford the best option?**
   - Check if costs fit within budget
   - Consider cash flow timing

3. **Are there any must-haves?**
   - Critical delivery dates?
   - Specific supplier requirements?

---

### Step 9: Choose Your Preferred Proposal

**For your first run, I recommend:**

👉 **Choose the "Balanced Strategy"** 

**Why?**
- Good middle ground
- Considers all factors
- Usually the safest choice
- Easy to explain to stakeholders

**How to choose:**
1. Click on the "Balanced Strategy" tab
2. Review the decisions
3. Note the total cost
4. (Later) You'll be able to save these decisions

---

### Step 10: Understanding the Results

**What if I got "FEASIBLE" instead of "OPTIMAL"?**
```
Status: FEASIBLE
```
This is FINE! It means:
- ✅ A valid solution was found
- ✅ All constraints are satisfied
- ⚠️ Might not be the absolute best possible
- 💡 Increase time_limit_seconds for next run

**What if some proposals are missing?**
```
Proposals: 3 (instead of 5)
```
This is OK! It means:
- Some strategies didn't complete in time
- The ones that completed are still valid
- Increase time_limit_seconds to get all 5

**What if optimization failed?**
```
Status: INFEASIBLE
```
This means:
- ❌ No solution satisfies all constraints
- Common causes:
  - Budget too tight
  - Locked decisions conflict
  - No procurement options for some items
- 💡 See [Troubleshooting](#troubleshooting) section

---

## 🎓 Next Steps

After your first successful run:

### **Today:**
1. ✅ Successfully ran first optimization
2. ✅ Understood all 5 strategies
3. ✅ Identified preferred proposal
4. 📝 Document your chosen strategy

### **This Week:**
1. Try different solvers:
   - Run with GLOP → compare speed
   - Run with CBC → compare results
2. Adjust time limits
3. Test with real project data

### **Next Week:**
1. Run optimizations regularly
2. Integrate into workflow
3. Train team on using results
4. Set up production configuration

---

## 🔧 Customizing Your Next Run

### **Scenario 1: I Need Results Faster**

```
Configuration:
- Solver Type: GLOP (5-10x faster!)
- Time Limit: 60 seconds
- Generate Multiple Proposals: No
- Strategies: LOWEST_COST
```

**Expected:** Results in 10-20 seconds

---

### **Scenario 2: I Need True Optimal Solution**

```
Configuration:
- Solver Type: CP_SAT or CBC
- Time Limit: 600 seconds (10 minutes)
- Generate Multiple Proposals: No
- Strategies: PRIORITY_WEIGHTED
```

**Expected:** Guaranteed optimal (if completes)

---

### **Scenario 3: I Want to Explore All Options**

```
Configuration:
- Solver Type: CP_SAT
- Time Limit: 300 seconds
- Generate Multiple Proposals: Yes
- Strategies: (empty - all strategies)
```

**Expected:** 5 proposals to compare

---

### **Scenario 4: Large Project (100+ items)**

```
Configuration:
- Solver Type: GLOP (only one fast enough)
- Time Limit: 300 seconds
- Generate Multiple Proposals: No
- Strategies: LOWEST_COST or PRIORITY_WEIGHTED
```

**Expected:** Results in 30-60 seconds

---

## 📊 Adding Test Data

Don't have test data yet? Here's how to add it quickly:

### **Option 1: Use Seed Data (if available)**

```powershell
cd backend
python -m app.seed_data
```

### **Option 2: Manual Entry via UI**

1. **Add a Project:**
   - Navigate to "Projects"
   - Click "Add Project"
   - Fill in: Project Code, Name, Priority (1-10)
   - Click "Create"

2. **Add Project Items:**
   - Click on your project
   - Click "Add Item"
   - Fill in: Item Code, Quantity, Delivery Options
   - Example delivery options: `["2025-11-01", "2025-12-01", "2026-01-01"]`
   - Click "Create"
   - Repeat for 5-10 items

3. **Add Procurement Options:**
   - Navigate to "Procurement"
   - Click "Add Option"
   - Fill in: Item Code (must match project item), Supplier, Cost, Lead Time
   - Click "Create"
   - Add 2-3 options per item code

4. **Add Budget Data:**
   - Navigate to "Finance"
   - Click "Add Budget"
   - Fill in: Date (e.g., 2025-11-01), Amount (e.g., 50000)
   - Click "Create"
   - Add budget for 3-6 periods

---

## 🐛 Troubleshooting

### **Problem: Page shows "No solver information"**

**Solution:**
1. Check backend is running
2. Check browser console for errors
3. Try refreshing the page
4. Verify `/finance/solver-info` endpoint works

---

### **Problem: "INFEASIBLE" result**

**Possible Causes & Solutions:**

**1. Budget too tight:**
```
Solution: Increase budget amounts in Finance page
```

**2. No procurement options:**
```
Solution: Add procurement options for all item codes
```

**3. Locked decisions conflict:**
```
Solution: Review and unlock conflicting decisions
```

**4. Invalid delivery options:**
```
Solution: Check delivery_options field has valid dates
```

---

### **Problem: Optimization times out**

**Solutions:**
1. Reduce max_time_slots (try 6 instead of 12)
2. Increase time_limit_seconds (try 600)
3. Switch to GLOP solver (much faster)
4. Disable multiple proposals
5. Reduce problem size (fewer items)

---

### **Problem: Different runs give different results**

**This is normal!**
- CP-SAT may break ties differently
- GLOP uses LP relaxation (approximate)
- Different strategies have different objectives
- All are valid solutions

---

## 📞 Getting Help

**If stuck:**
1. Check `OR_TOOLS_QUICK_REFERENCE.md`
2. Review `SOLVER_DEEP_DIVE.md`
3. Check backend logs for error messages
4. Verify test data exists
5. Try with GLOP solver (simpler, faster)

---

## 🎉 Success Criteria

You've successfully completed your first run if:

- ✅ Optimization page loaded
- ✅ Configuration dialog opened
- ✅ Optimization completed (any status)
- ✅ Results displayed
- ✅ Can switch between proposal tabs
- ✅ Can view decision details

**Congratulations! You're now ready to use advanced optimization in production! 🚀**

---

## 📝 Record Your First Run

**Document for future reference:**

```
First Optimization Run - [Date]
================================

Configuration:
- Solver: CP_SAT
- Time Limit: 120 seconds
- Proposals Generated: 5
- Strategies: All

Results:
- Status: OPTIMAL / FEASIBLE
- Total Cost: $[amount]
- Items Optimized: [count]
- Execution Time: [seconds]

Chosen Proposal:
- Strategy: [name]
- Reason: [why you chose it]

Lessons Learned:
- [what worked well]
- [what to improve next time]
- [configuration adjustments needed]

Next Steps:
- [plan for next optimization run]
```

---

**Your optimization journey has begun! 🎯**

*Remember: The first run is about learning. Perfection comes with practice!*

