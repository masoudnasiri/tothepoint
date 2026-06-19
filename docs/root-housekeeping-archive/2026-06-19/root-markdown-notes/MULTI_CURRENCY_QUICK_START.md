# 💰 Multi-Currency Budget - Quick Start

## 🚀 **5-Minute Quick Start Guide**

---

## ✅ **Platform Status**
✅ **All services running successfully**
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Database: PostgreSQL running

---

## 📍 **Where to Go**

1. Open browser: `http://localhost:3000`
2. Login with your credentials
3. Navigate to: **Finance Management**
4. You'll see two tabs:
   - **Budget Management** ← You're here for multi-currency budgets
   - **Currency Management** ← Manage currencies and exchange rates

---

## 🎯 **Quick Actions**

### **1️⃣ Add a Multi-Currency Budget (30 seconds)**

```
1. Click "Add Budget" button (top right)
2. Select date: [Pick a date]
3. Enter Base Budget (IRR): 50000000000
4. Click "Add Currency Budget" dropdown
5. Select "USD"
6. Enter: 100000
7. (Optional) Add more currencies
8. Click "Add Budget"
```

**Result**: Budget created with IRR base + USD allocation! 🎉

---

### **2️⃣ View Budget Summary (5 seconds)**

**Look at the top section - you'll see:**
- 🔵 Total Periods: 5
- 🟢 Base Budget (IRR): $2,500,000.00
- 🔵 USD: $500,000.00
- 🔵 EUR: €400,000.00

**Each chip shows total for that currency across all periods.**

---

### **3️⃣ Edit Existing Budget (20 seconds)**

```
1. Click ✏️ (edit icon) on any budget row
2. Change amounts or add/remove currencies
3. Click "Update Budget"
```

---

### **4️⃣ View Multi-Currency Budgets in Table**

**Each row shows:**
- Budget Date
- Base Budget (IRR) - Main amount
- Multi-Currency Budgets - Colorful chips showing: `USD: $50K` `EUR: €40K`
- Created date
- Actions (Edit/Delete)

---

## 💡 **Key Concepts (3 bullets)**

1. **Base Budget (IRR)**: Always required - used for optimization
2. **Multi-Currency Budgets**: Optional - for specific currency allocations
3. **Summary Totals**: Automatically calculated for each currency

---

## 🎨 **What You'll See**

### **Budget Summary Box**
```
┌─────────────────────────────────────┐
│ Budget Summary                      │
│                                     │
│ [Total Periods: 3]                 │
│ [Base Budget (IRR): $150M]         │
│ [USD: $300K] [EUR: €250K]          │
└─────────────────────────────────────┘
```

### **Budget Table Row**
```
10/15/2025 | $50M | [USD: $100K] [EUR: €80K] | 10/11/25 | [✏️] [🗑️]
```

---

## 📋 **Common Scenarios**

### **Scenario A: Single Currency Project**
```
Base Budget (IRR): 50,000,000,000
Multi-Currency: USD: 100,000
```
Use when: You have a specific USD allocation

### **Scenario B: Multi-National Project**
```
Base Budget (IRR): 100,000,000,000
Multi-Currency: 
  - USD: 200,000
  - EUR: 150,000
  - AED: 550,000
```
Use when: Different regions use different currencies

### **Scenario C: Simple Budget**
```
Base Budget (IRR): 50,000,000,000
Multi-Currency: (none)
```
Use when: Everything in base currency

---

## 🔧 **Before You Start**

### **Step 1: Setup Currencies (One-time, 2 minutes)**
1. Go to **Currency Management** tab
2. Verify these currencies are active:
   - ✅ IRR (Iranian Rial) - Base currency
   - ✅ USD (US Dollar)
   - ✅ EUR (Euro)
   - ✅ AED (UAE Dirham)
3. Update exchange rates if needed

### **Step 2: Test Budget (1 minute)**
1. Go to **Budget Management** tab
2. Click **Add Budget**
3. Enter any date and amounts
4. Add one currency (e.g., USD)
5. Save and verify it appears

### **Step 3: Start Using!**
You're ready! Create budgets for your actual periods.

---

## ⚡ **Tips & Tricks**

### **Tip 1: Adding Multiple Currencies**
- Keep selecting from "Add Currency Budget" dropdown
- Each selection adds a new currency input
- Remove any currency with the "Remove" button

### **Tip 2: Formatting**
- Don't worry about commas - system adds them automatically
- Currency symbols ($ € ﷼) display automatically
- Large numbers show as "50K", "1M" in chips

### **Tip 3: Editing**
- Click ✏️ to edit any budget
- All currencies are editable
- Date cannot be changed (unique identifier)

### **Tip 4: Summary**
- Summary cards update automatically
- Shows totals across ALL budget periods
- Each currency calculated separately

---

## 🎯 **Example: Complete Workflow**

### **Your Task**: Add Q1 2025 budgets with multi-currency

```
Step 1: Add January Budget
- Date: 2025-01-01
- Base: 50,000,000,000 IRR
- USD: 100,000
- EUR: 80,000

Step 2: Add February Budget
- Date: 2025-02-01
- Base: 45,000,000,000 IRR
- USD: 90,000
- EUR: 75,000

Step 3: Add March Budget
- Date: 2025-03-01
- Base: 55,000,000,000 IRR
- USD: 110,000
- EUR: 85,000

Result:
Summary shows:
- Total Periods: 3
- Base Budget: $150,000,000,000 IRR
- USD: $300,000
- EUR: €240,000
```

---

## 🎨 **Dialog Preview**

### **When You Click "Add Budget"**
You'll see a dialog with:
1. **Budget Date picker** (top)
2. **Base Budget input** (required)
3. **Divider** with "Multi-Currency Budgets (Optional)"
4. **Currency inputs** (dynamic, based on what you add)
5. **Dropdown** to add more currencies
6. **Cancel/Add buttons** (bottom)

---

## 🔒 **Who Can Do What**

| Role        | View Budgets | Add/Edit Budgets | Delete Budgets |
|-------------|--------------|------------------|----------------|
| Admin       | ✅           | ✅               | ✅             |
| Finance     | ✅           | ✅               | ✅             |
| PM          | ✅           | ❌               | ❌             |
| Procurement | ✅           | ❌               | ❌             |

---

## 🐛 **Quick Fixes**

### **Problem**: No currencies in dropdown
**Fix**: Go to Currency Management → Activate currencies

### **Problem**: Can't save budget
**Fix**: Ensure Base Budget (IRR) is entered (required field)

### **Problem**: Currency not showing
**Fix**: Refresh page, check currency is active

### **Problem**: Wrong exchange rate
**Fix**: Currency Management → Update exchange rate

---

## 📊 **What Data is Stored**

```json
{
  "budget_date": "2025-01-15",
  "available_budget": 50000000000,
  "multi_currency_budget": {
    "USD": 100000,
    "EUR": 80000,
    "AED": 400000
  }
}
```

- **budget_date**: Unique date for this budget period
- **available_budget**: Base currency amount (IRR)
- **multi_currency_budget**: Object with currency codes as keys

---

## ✅ **Success Checklist**

After adding your first multi-currency budget, verify:

- [ ] Budget appears in table
- [ ] Multi-Currency chips display correctly
- [ ] Summary totals are calculated
- [ ] Currency symbols show ($ € ﷼)
- [ ] Edit button works
- [ ] Can add more currencies when editing
- [ ] Can remove currencies
- [ ] Summary updates after changes

**If all checked - you're good to go! 🎉**

---

## 🚀 **You're Ready!**

**Platform is live at: http://localhost:3000**

1. Login
2. Go to Finance → Budget Management
3. Start creating multi-currency budgets!

---

**Need more details? See: `MULTI_CURRENCY_BUDGET_GUIDE.md`**

*Last Updated: October 11, 2025*

