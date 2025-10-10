# 📋 Quick Test Guide - New Optimization Engine

## 🚀 How to Test the Fixed Optimization

### 1. Restart the Platform
```bash
docker-compose restart backend
```

### 2. Login to the Platform
- URL: `http://localhost:3000`
- Username: `admin`
- Password: `admin123`

### 3. Run Basic Optimization

**Navigate to:** Optimization Page

**Click:** "Run Optimization" button

**Expected Results:**
```
✅ Solution found
✅ 150-250 items purchased (out of 310 total)
✅ Total cost: $12-14M
✅ Solve time: 5-30 seconds
```

### 4. Run Advanced Optimization

**Click:** "Advanced Optimization" button

**Select:** "Multi-solver optimization with strategy comparison"

**Expected Results:**
```
✅ Multiple proposals generated
✅ Each strategy produces DIFFERENT results:
   - LOWEST_COST: Cheapest options, may delay some items
   - PRIORITY_WEIGHTED: High-priority projects first
   - FAST_DELIVERY: Earliest possible delivery
   - SMOOTH_CASHFLOW: Evenly distributed spending
   - BALANCED: Best overall trade-off
```

### 5. Verify Strategy Differences

Compare the proposals:
- **Different suppliers** chosen for same items
- **Different total costs** (should vary by 5-15%)
- **Different delivery timelines**
- **Different project prioritization**

---

## 🎯 What Success Looks Like

### ✅ Good Results:
- Items purchased: 150-280 (48-90% of total)
- Total cost: $10-15M (within or slightly over budget)
- Revenue (15% markup): $11.5-17.25M
- Profit margin: ~15%
- Solution time: < 60 seconds

### ❌ Red Flags:
- Items purchased: 0 or < 50
- Total cost: $0 or > $20M
- All strategies produce identical results
- Solution time: > 120 seconds

---

## 🔍 Troubleshooting

### Problem: Still Getting 0 Items

**Check 1: Data Exists**
```bash
docker-compose exec -T backend python -c "from app.database import SessionLocal; from app.models import ProjectItem, ProcurementOption; db = SessionLocal(); print('Items:', db.query(ProjectItem).count()); print('Options:', db.query(ProcurementOption).count())"
```

**Expected:**
- Items: 310
- Options: 151

**Check 2: Pricing is Correct**
The seed data should have:
- Procurement costs: $50-2000 per unit
- Invoice amounts: 15% higher than costs
- You can verify this was fixed in the previous conversation

**Check 3: Backend Logs**
```bash
docker-compose logs backend | Select-String "objective\|slack\|value"
```

Look for:
- "Set objective: Minimize(Cost - Value + Budget_Penalty)"
- "budget_slack_" variables created

---

## 📊 Understanding the Results

### Cost Breakdown:
```
Total Procurement Cost: $13.2M
├─ Items: 210 @ avg $62,857 each
├─ Discounts: -$450K (bundle discounts)
└─ Payment Terms: Various (cash/installments)
```

### Revenue Breakdown:
```
Total Revenue: $15.18M
├─ Base: $13.2M (procurement cost)
└─ Markup: +$1.98M (15% profit)
```

### Budget Utilization:
```
Available Budget: $14.15M
Actual Spending: $13.2M
Utilization: 93.3%
Over-Budget Penalty: $0 (within budget!)
```

---

## 🎨 Key Differences Between Strategies

### LOWEST_COST
- **Goal:** Minimize total spending
- **Selects:** Cheapest suppliers
- **May compromise:** Delivery speed, priorities
- **Best for:** Tight budget constraints

### PRIORITY_WEIGHTED
- **Goal:** Complete high-priority projects first
- **Selects:** Items from priority 9-10 projects
- **May compromise:** Cost, delivery speed
- **Best for:** Mission-critical projects

### FAST_DELIVERY
- **Goal:** Get items delivered ASAP
- **Selects:** Suppliers with shortest lead times
- **May compromise:** Cost
- **Best for:** Time-sensitive projects

### SMOOTH_CASHFLOW
- **Goal:** Evenly distribute spending over time
- **Selects:** Mix of early and late deliveries
- **May compromise:** Individual project timelines
- **Best for:** Cash flow management

### BALANCED
- **Goal:** Best overall trade-off
- **Considers:** Priority (70%) + Delivery (30%)
- **Recommended for:** Most use cases

---

## 💡 Pro Tips

1. **Compare Multiple Strategies:**
   - Run all 5 strategies
   - Review side-by-side in the UI
   - Choose the one that best fits your needs

2. **Check Financial Impact:**
   - Navigate to Finance Page
   - View "Cash Flow Forecast"
   - Ensure no month exceeds budget significantly

3. **Manual Adjustments:**
   - After optimization, you can edit individual decisions
   - Add/remove items from the proposal
   - System will warn if you exceed budget (future feature)

4. **Finalize Decisions:**
   - Review the proposal carefully
   - Click "Finalize" to lock in your choices
   - This creates cash flow events and updates project status

---

## 📞 Need Help?

**Common Issue:** "Optimization takes too long (> 2 minutes)"
**Solution:** Reduce time limit to 30 seconds or increase to 120 seconds

**Common Issue:** "No proposals generated"
**Solution:** Check that seed data has been loaded correctly (see "Check 1" above)

**Common Issue:** "All strategies are identical"
**Solution:** This was the old bug - should be fixed now. If persists, check backend logs.

---

## ✅ Success Checklist

- [ ] Platform restarted
- [ ] Can login as admin
- [ ] Basic optimization runs successfully
- [ ] Advanced optimization generates multiple proposals
- [ ] Each strategy produces different results
- [ ] Total cost is realistic ($10-15M range)
- [ ] Can view proposals in the UI
- [ ] Can finalize a proposal

---

**Last Updated:** October 10, 2025  
**Version:** 2.0 (Post-Fix)  
**Status:** ✅ Ready for Testing

