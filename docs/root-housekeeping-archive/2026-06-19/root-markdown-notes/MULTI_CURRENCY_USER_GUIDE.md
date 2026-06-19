# 🌍 Multi-Currency System - Complete User Guide

## Overview

The platform now supports multiple currencies (IRR, USD, EUR, GBP, JPY, etc.) for procurement, invoicing, and financial reporting. This guide explains how to set up and use the multi-currency features.

---

## 📋 Table of Contents

1. [Currency Management Setup](#1-currency-management-setup)
2. [Exchange Rate Management](#2-exchange-rate-management)
3. [Multi-Currency Budgets](#3-multi-currency-budgets)
4. [Dashboard Currency Views](#4-dashboard-currency-views)
5. [Multi-Currency Procurement](#5-multi-currency-procurement)
6. [Analytics & Reports](#6-analytics--reports)
7. [Best Practices](#7-best-practices)

---

## 1. Currency Management Setup

### Step 1: Access Currency Management
1. Log in as **Finance** or **Admin** user
2. Navigate to **Finance Management** → **Currency Management** tab
3. You'll see the currency management interface

### Step 2: View Available Currencies
The platform comes with pre-configured currencies:
- **IRR** (Iranian Rial) - Base Currency ⭐
- **USD** (US Dollar)
- **EUR** (Euro)
- **GBP** (British Pound)
- **JPY** (Japanese Yen)

**Note:** IRR is the **base currency** - all financial aggregations and optimizations convert to IRR.

### Step 3: Add New Currency (Optional)
If you need a currency not in the list:
1. Click **"Add New Currency"** button
2. Fill in the form:
   - **Currency Code**: 3-letter code (e.g., AED, CAD)
   - **Currency Name**: Full name (e.g., UAE Dirham)
   - **Symbol**: Currency symbol (e.g., د.إ, $)
   - **Decimal Places**: Number of decimals (usually 2, but 0 for IRR)
3. Click **Save**

**Example:**
```
Code: AED
Name: UAE Dirham
Symbol: د.إ
Decimal Places: 2
```

---

## 2. Exchange Rate Management

### Why Exchange Rates Matter
Exchange rates are **time-variant** - they change daily. The system uses the exchange rate **valid on the transaction date** for accurate conversions.

### Step 1: Add Exchange Rates
1. Go to **Finance Management** → **Currency Management** tab
2. Scroll to **Exchange Rates** section
3. Click **"Add Exchange Rate"** button

### Step 2: Fill Exchange Rate Form
- **Date**: Select the date for this rate
- **From Currency**: Select source currency (e.g., USD)
- **To Currency**: Usually IRR (base currency)
- **Exchange Rate**: Enter the conversion rate

**Example:**
```
Date: 2025-10-11
From: USD
To: IRR
Rate: 50000.00
```
This means: 1 USD = 50,000 IRR on October 11, 2025

### Step 3: Update Rates Regularly
**Important:** Exchange rates change daily. You should:
- Add new rates daily or weekly
- Edit existing rates if corrections are needed
- The system uses the **closest available date** for conversions

### Common Exchange Rate Setup
```
Date: 2025-10-11
USD → IRR: 50,000
EUR → IRR: 55,000
GBP → IRR: 62,000
JPY → IRR: 350
```

---

## 3. Multi-Currency Budgets

### Understanding Budget Structure
Each budget period (month) can have:
1. **Base Budget** (IRR) - The primary budget
2. **Additional Currency Budgets** - Optional budgets in other currencies

### Step 1: Create Base Budget
1. Go to **Finance Management** → **Budget Management** tab
2. Click **"Add Budget"**
3. Fill in:
   - **Budget Date**: Select month (e.g., 2025-11-01)
   - **Available Budget (IRR)**: Enter amount in IRR

**Example:**
```
Budget Date: 2025-11-01
Available Budget: 5,000,000,000 IRR
```

### Step 2: Add Multi-Currency Budget (Optional)
1. In the same form, scroll to **"Multi-Currency Budget"**
2. Click **"Add Currency Budget"**
3. Select currency and enter amount
4. Click **"+"** to add
5. Repeat for other currencies

**Example Multi-Currency Budget:**
```
Base: 5,000,000,000 IRR
Additional:
  - USD: 100,000
  - EUR: 50,000
```

### Step 3: View Budget Summary
After saving, you'll see:
- **Base Budget**: Shows IRR amount
- **Multi-Currency**: Shows additional currencies as chips
- **Period Count**: Number of budget periods

### Editing Budgets
1. Click **Edit** button on any budget row
2. Modify base budget or currency budgets
3. To remove a currency: Click the **"×"** on the currency chip
4. Click **Save Changes**

---

## 4. Dashboard Currency Views

### Two Display Modes

The Dashboard offers two ways to view financial data:

#### Mode 1: **UNIFIED (IRR)** - Default ⭐
Shows all financial data **converted to IRR** using exchange rates.

**When to use:**
- Executive overview
- Total cost analysis
- Budget vs. actual comparisons
- Cross-project summaries

**What you see:**
- Single summary card set (Total Inflow, Outflow, Net Position, Final Balance)
- Single combined chart
- All amounts in IRR (﷼)

#### Mode 2: **ORIGINAL CURRENCIES**
Shows financial data **separated by currency** - no conversion.

**When to use:**
- Detailed currency breakdown
- Foreign currency tracking
- Multi-currency cash flow planning
- Identifying currency exposure

**What you see:**
- Separate summary cards **for each currency**
- Separate charts **for each currency**
- Amounts in original currency (USD $, EUR €, IRR ﷼)

### Switching Between Modes

**Location:** Top of Dashboard page

**How to switch:**
1. Look for currency selector chips at the top
2. Click **"UNIFIED (IRR)"** for consolidated view
3. Click **"ORIGINAL CURRENCIES"** for separated view

**Visual Example:**
```
┌─────────────────────────────────────┐
│ [UNIFIED (IRR)] [ORIGINAL CURRENCIES] │  ← Click to switch
└─────────────────────────────────────┘
```

### Understanding Unified Mode

**Conversion Logic:**
- Uses exchange rates from the transaction date
- Converts USD, EUR, etc. to IRR
- Aggregates all currencies into single IRR amounts

**Example:**
```
Transaction 1: $1,000 on Oct 11 (rate: 50,000) = 50,000,000 IRR
Transaction 2: €500 on Oct 11 (rate: 55,000) = 27,500,000 IRR
Transaction 3: 10,000,000 IRR on Oct 11 = 10,000,000 IRR
───────────────────────────────────────────────────────────
Total: 87,500,000 IRR
```

### Understanding Original Currency Mode

**Display Logic:**
- Groups transactions by currency
- Shows separate summary for each currency
- No conversion applied

**Example Display:**
```
IRR Summary
  Inflow: 100,000,000 ﷼
  Outflow: 50,000,000 ﷼
  Net: 50,000,000 ﷼

USD Summary
  Inflow: $10,000
  Outflow: $5,000
  Net: $5,000

EUR Summary
  Inflow: €5,000
  Outflow: €2,000
  Net: €3,000
```

### Dashboard Budget Display

**Unified Mode:**
- Converts all currency budgets to IRR
- Shows combined budget total

**Original Mode:**
- Shows IRR base budget in IRR section
- Shows USD budget in USD section
- Shows EUR budget in EUR section

---

## 5. Multi-Currency Procurement

### Procurement Options with Currency

**When adding procurement options:**
1. Go to **Procurement Plan** page
2. Click **"Add New Procurement Option"**
3. Fill in details:
   - Item Code
   - Supplier Name
   - **Currency**: Select from dropdown (USD, EUR, IRR, etc.)
   - **Cost**: Enter cost in selected currency
   - Lead Time
   - Payment Terms

**Example:**
```
Supplier: ABC Corporation
Item: Steel Beams
Currency: USD
Cost: $1,500 per unit
Lead Time: 30 days
```

### Currency in Finalized Decisions

When finalizing decisions:
- Currency is automatically inherited from procurement option
- Invoice amounts use the same currency
- Payment amounts use the same currency

### Optimization with Multi-Currency

**How optimization handles currencies:**
1. Reads procurement option costs in original currency
2. Converts all costs to IRR using exchange rates
3. Runs optimization in IRR (base currency)
4. Stores decisions with original currency preserved

**Why this matters:**
- Optimization compares costs fairly (apples to apples in IRR)
- Original currency is preserved for procurement
- Exchange rate on **purchase date** is used

---

## 6. Analytics & Reports

### Analytics Page - Always Unified

**Important:** The Analytics & Forecast page **always uses unified IRR data**.

**Why:**
- EVM (Earned Value Management) requires consistent currency
- Forecasting needs single currency baseline
- KPIs (CPI, SPI) must be calculated in one currency

**Metrics shown:**
- BAC (Budget at Completion) - in IRR
- EV (Earned Value) - in IRR
- PV (Planned Value) - in IRR
- AC (Actual Cost) - in IRR
- CPI, SPI - dimensionless ratios

### Reports Page - Always Unified

**Reports also use unified IRR data:**
- Consistent reporting
- Executive summaries
- Excel exports in single currency

---

## 7. Best Practices

### ✅ DO:

1. **Set up exchange rates before transactions**
   - Add rates for the current month
   - Update weekly or daily
   - Cover all currencies you'll use

2. **Use consistent currency for suppliers**
   - If supplier quotes in USD, always use USD
   - Don't mix currencies for same supplier

3. **Review budgets in both modes**
   - Unified mode: Overall financial health
   - Original mode: Currency exposure analysis

4. **Document exchange rate sources**
   - Use official bank rates
   - Note the rate source in notes field
   - Keep rate history

5. **Regular currency reconciliation**
   - Monthly: Check currency balances
   - Compare original vs. unified reports
   - Verify exchange rate accuracy

### ❌ DON'T:

1. **Don't ignore exchange rate updates**
   - Stale rates = Incorrect conversions
   - Always update rates before month-end

2. **Don't mix currencies arbitrarily**
   - Maintain currency consistency per supplier
   - Don't switch currency mid-project

3. **Don't forget base budget (IRR)**
   - Multi-currency budgets are additional
   - Base budget in IRR is required

4. **Don't rely only on original currency mode for decisions**
   - Use unified mode for strategic decisions
   - Original mode is for detailed tracking

5. **Don't delete currencies with transactions**
   - Inactive currencies should be marked inactive
   - Deletion may break historical data

---

## 🎯 Quick Start Checklist

### Initial Setup (One-time)
- [ ] Review available currencies
- [ ] Add missing currencies if needed
- [ ] Set up initial exchange rates for current month
- [ ] Create base budgets in IRR

### Monthly Tasks
- [ ] Update exchange rates for new month
- [ ] Add budget for new month
- [ ] Review previous month's currency performance
- [ ] Check for currency exposure

### Daily Operations
- [ ] Select appropriate currency when adding procurement options
- [ ] Use unified view for executive decisions
- [ ] Use original view for detailed tracking
- [ ] Update exchange rates if significant changes occur

---

## 💡 Tips & Tricks

### Tip 1: Fast Exchange Rate Updates
Create a spreadsheet with common rates, copy-paste into the form daily.

### Tip 2: Currency Exposure Analysis
Use Original Currency mode to see which currencies you're most exposed to.

### Tip 3: Optimization Strategy
If you want to minimize foreign currency risk, add more IRR-based procurement options.

### Tip 4: Budget Planning
Set multi-currency budgets based on expected foreign currency procurement needs.

### Tip 5: Dashboard Quick Toggle
Bookmark the dashboard with your preferred currency view mode.

---

## 🆘 Troubleshooting

### Problem: "Exchange rates not found"
**Solution:** Add exchange rates for the transaction date or earlier dates.

### Problem: Dashboard shows empty in original mode
**Solution:** No transactions in foreign currencies yet. All transactions are in IRR.

### Problem: Optimization fails with currency error
**Solution:** Ensure all procurement options have valid currency_id set.

### Problem: Budget not showing in currency breakdown
**Solution:** Make sure you've added multi-currency budget, not just base budget.

### Problem: Wrong conversion amounts
**Solution:** Check exchange rate for that specific date. Update if incorrect.

---

## 📞 Need Help?

- **For Currency Setup:** Contact Finance team
- **For Technical Issues:** Contact System Administrator
- **For Exchange Rate Sources:** Contact Finance Manager

---

**Document Version:** 1.0  
**Last Updated:** October 11, 2025  
**Prepared by:** AI Assistant based on Multi-Currency Architecture Implementation

---

## Appendix: Currency Codes Reference

| Code | Name | Symbol | Decimal Places |
|------|------|--------|----------------|
| IRR | Iranian Rial | ﷼ | 0 |
| USD | US Dollar | $ | 2 |
| EUR | Euro | € | 2 |
| GBP | British Pound | £ | 2 |
| JPY | Japanese Yen | ¥ | 0 |
| AED | UAE Dirham | د.إ | 2 |
| SAR | Saudi Riyal | ﷼ | 2 |
| CNY | Chinese Yuan | ¥ | 2 |
| TRY | Turkish Lira | ₺ | 2 |

---

**End of Guide**

