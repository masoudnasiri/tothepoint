# 📚 Procurement DSS - Complete User Guide

## 🎯 System Overview

The **Project Procurement & Financial Optimization Decision Support System (DSS)** helps construction project managers optimize procurement decisions by:
- Managing multiple construction projects
- Tracking items needed for each project
- Evaluating supplier options
- Managing budgets across time periods
- Running optimization to minimize costs

---

## 🔐 User Roles & Access

| Role | Username | Password | Permissions |
|------|----------|----------|-------------|
| **Admin** | admin | admin123 | Full access to all features |
| **Project Manager** | pm1 | pm123 | Manage projects and items |
| **Procurement** | proc1 | proc123 | Manage supplier options |
| **Finance** | finance1 | finance123 | Manage budgets and run optimizations |

---

## 📋 Features Guide

### 1. 📊 Dashboard

**Access:** All users

**What it shows:**
- Total projects count
- Total items count  
- Total procurement options
- Recent activity

**How to use:**
1. Login with your credentials
2. View the dashboard overview
3. Click on any metric card for details

---

### 2. 🏗️ Projects Management

**Access:** Admin, Project Manager

**Purpose:** Create and manage construction projects

**Sample Data:**
- PROJ001: Highway Extension
- PROJ002: City Center Development

**How to create a new project:**
1. Navigate to **Projects** from sidebar
2. Click **"Add Project"** button
3. Fill in:
   - Project Code (e.g., PROJ003)
   - Project Name (e.g., Bridge Construction)
4. Click **"Create"**

**How to edit/delete:**
- Click the **Edit** icon (pencil) to modify
- Click the **Delete** icon (trash) to remove

---

### 3. 📦 Project Items Management

**Access:** Admin, Project Manager

**Purpose:** Define items needed for each project with timing requirements

**Sample Data:**
- Item: Steel Beam (STL-001)
  - Quantity: 100 units
  - Must buy time: Period 3
  - Allowed times: [1,2,3]

**How to add items to a project:**
1. Navigate to **Project Items**
2. Click **"Add Item"**
3. Fill in:
   - **Project**: Select from dropdown
   - **Item Code**: e.g., STL-001
   - **Item Name**: e.g., Steel Beam Type A
   - **Quantity**: How many units needed
   - **Must Buy Time**: Latest period to purchase
   - **Allowed Times**: Comma-separated periods (e.g., 1,2,3)
   - **External Purchase**: Can this be bought from outside? (Yes/No)
4. Click **"Create"**

**Excel Import/Export:**
- Click **"Download Template"** to get Excel template
- Fill in the template with multiple items
- Click **"Import from Excel"** to upload
- Click **"Export to Excel"** to download current items

---

### 4. 🚚 Procurement Options

**Access:** Admin, Procurement Officer

**Purpose:** Define supplier options for each item with pricing and terms

**Sample Data:**
- Item STL-001 from Supplier A:
  - Base cost: $150/unit
  - Lead time: 2 periods
  - Discount: 5% for orders ≥ 50 units
  - Payment: Cash

**How to add procurement options:**
1. Navigate to **Procurement**
2. Click **"Add Option"**
3. Fill in:
   - **Item Code**: Must match item code from Project Items
   - **Supplier Name**: e.g., ABC Steel Co.
   - **Base Cost**: Price per unit
   - **Lead Time**: Periods needed for delivery
   - **Discount Threshold**: Minimum quantity for discount
   - **Discount Percentage**: Discount amount (e.g., 5 for 5%)
   - **Payment Terms**: Cash or Credit
4. Click **"Create"**

**Tips:**
- Create multiple options for the same item code to compare suppliers
- Lower base cost + discounts = better optimization results
- Shorter lead times = more flexibility

**Excel Import/Export:**
- Use Excel templates for bulk import/export

---

### 5. 💰 Finance & Budget Management

**Access:** Admin, Finance Manager

**Purpose:** Set budget constraints for each time period

**Sample Data:**
- Period 1: $50,000 budget
- Period 2: $75,000 budget
- Period 3: $100,000 budget

**How to manage budgets:**
1. Navigate to **Finance**
2. Click **"Add Budget"**
3. Fill in:
   - **Time Slot**: Period number (e.g., 1)
   - **Available Budget**: Amount in dollars
4. Click **"Create"**

**Budget Dashboard:**
- View total budget across all periods
- See budget utilization percentage
- Track spending by period

**Excel Import/Export:**
- Quickly import budgets from Excel files

---

### 6. ⚡ Optimization Engine

**Access:** Admin, Finance Manager

**Purpose:** Run optimization to find the best procurement strategy

**What it does:**
The optimization algorithm:
1. ✅ Analyzes all project items and their requirements
2. ✅ Evaluates all procurement options
3. ✅ Considers budget constraints per period
4. ✅ Accounts for lead times and delivery schedules
5. ✅ Applies bulk discounts where applicable
6. ✅ Optimizes payment terms (cash vs credit)
7. ✅ Minimizes total procurement cost

**How to run optimization:**

1. **Prepare Your Data** (already done with sample data):
   - ✅ Create projects
   - ✅ Add project items with timing requirements
   - ✅ Define procurement options for each item
   - ✅ Set budget limits

2. **Run Optimization:**
   - Navigate to **Optimization** page
   - Click **"Run Optimization"** button
   - Configure parameters:
     - **Max Time Slots**: 12 (default)
     - **Time Limit**: 300 seconds (default)
   - Click **"Run Optimization"**

3. **Wait for Results:**
   - Progress indicator shows optimization is running
   - Usually takes 5-60 seconds depending on problem size
   - Alert will show when complete

4. **Review Results:**
   - **Status**: OPTIMAL / FEASIBLE / INFEASIBLE
   - **Total Cost**: Minimized total procurement cost
   - **Items Optimized**: Number of items processed
   - **Execution Time**: How long it took

5. **Analyze Purchase Schedule:**
   - View detailed table showing:
     - Which items to buy
     - From which suppliers (implicitly)
     - When to purchase (period)
     - When delivery occurs
     - Quantities and costs

**Optimization Results Interpretation:**

**OPTIMAL Status:**
```
✅ Best possible solution found
✅ No better solution exists
✅ All constraints satisfied
✅ Minimum cost achieved
```

**FEASIBLE Status:**
```
⚠️ Valid solution found
⚠️ May not be the absolute best
⚠️ All constraints satisfied
⚠️ Time limit reached before proving optimality
```

**INFEASIBLE Status:**
```
❌ No solution exists
❌ Constraints are impossible to satisfy
❌ Possible reasons:
   - Budget too low
   - Lead times too long
   - Missing procurement options
   - Incompatible requirements
```

---

## 🎓 Example Workflow

### Scenario: Plan procurement for a new bridge project

1. **Create Project** (as PM):
   ```
   Code: BRIDGE-001
   Name: Downtown Bridge Construction
   ```

2. **Add Project Items** (as PM):
   ```
   Item 1: Steel Beams (STL-001)
   - Quantity: 200 units
   - Must buy: Period 4
   - Allowed: [1,2,3,4]

   Item 2: Concrete Mix (CON-001)
   - Quantity: 500 cubic yards
   - Must buy: Period 5
   - Allowed: [2,3,4,5]
   ```

3. **Add Procurement Options** (as Procurement):
   ```
   For STL-001:
   - Supplier A: $150/unit, lead 2, 5% off at 100+
   - Supplier B: $145/unit, lead 3, 10% off at 150+

   For CON-001:
   - Supplier C: $80/yard, lead 1, no discount
   - Supplier D: $75/yard, lead 2, 8% off at 300+
   ```

4. **Set Budgets** (as Finance):
   ```
   Period 1: $40,000
   Period 2: $60,000
   Period 3: $50,000
   Period 4: $70,000
   Period 5: $80,000
   ```

5. **Run Optimization** (as Finance/Admin):
   - Go to Optimization page
   - Click "Run Optimization"
   - Review results to see optimal purchase schedule

6. **Implement Plan:**
   - Follow the optimization results
   - Purchase items in the recommended periods
   - From the recommended suppliers (you can infer from costs)

---

## 💡 Tips & Best Practices

### For Project Managers:
- ✅ Plan items early in the project timeline
- ✅ Allow flexible purchase times when possible
- ✅ Use realistic quantity estimates
- ✅ Mark truly time-critical items appropriately

### For Procurement Officers:
- ✅ Add multiple supplier options per item
- ✅ Keep pricing data up to date
- ✅ Include accurate lead times
- ✅ Document bulk discount thresholds

### For Finance Managers:
- ✅ Set realistic budgets per period
- ✅ Allow some buffer for unexpected costs
- ✅ Run optimization before finalizing budgets
- ✅ Review results carefully before committing

### For Optimization:
- ✅ Ensure complete data before running
- ✅ Start with smaller time horizons for testing
- ✅ Save/export results for documentation
- ✅ Re-run if requirements change

---

## 🔧 Common Issues & Solutions

### No optimization results?
**Solution:** Make sure you have:
1. At least one project with items
2. Procurement options for all item codes
3. Budget data for relevant periods
4. Clicked "Run Optimization" button

### Infeasible optimization?
**Solution:** Check:
1. Budget is sufficient for required items
2. Lead times allow items to arrive on time
3. All item codes have procurement options
4. Allowed purchase times are reasonable

### Can't add items?
**Solution:** Ensure:
1. Project exists first
2. You're logged in as PM or Admin
3. All required fields are filled

---

## 📊 Current Sample Data

The system comes with sample data:

**Projects:**
- PROJ001: Highway Extension Project
- PROJ002: City Center Development

**Items:**
- Various construction materials (steel, concrete, etc.)
- Different quantities and timing requirements

**Suppliers:**
- Multiple options per item
- Various pricing and discount structures

**Budget:**
- 12 periods with varying budgets
- Total: ~$900,000 across all periods

**You can:**
- ✅ Use sample data to test optimization
- ✅ Add your own data
- ✅ Modify sample data
- ✅ Delete and start fresh

---

## 🚀 Quick Start Test

1. **Login**: Use `admin` / `admin123`
2. **View Data**: Check Projects, Items, Procurement, Finance pages
3. **Run Optimization**: Go to Optimization → Click "Run Optimization"
4. **Review Results**: See the optimized procurement schedule
5. **Experiment**: Add new items or modify budgets and re-run

---

## 📞 Need Help?

- Check this guide for step-by-step instructions
- Review sample data for examples
- Start with small test cases
- Contact system administrator for issues

---

**System is ready to use! Start by running an optimization with the sample data.** 🎉
