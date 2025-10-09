# 📊 Optimization Feature Guide

## Overview

The Procurement Optimization feature uses Linear Programming to find the optimal procurement strategy that minimizes total cost while respecting:
- Budget constraints per time period
- Project item requirements and deadlines
- Supplier discounts and payment terms
- Lead times and delivery schedules

## Prerequisites

To run an optimization, you need:

1. ✅ **Projects** - Created in the Projects page
2. ✅ **Project Items** - Items added to projects with:
   - Quantities needed
   - Required delivery times
   - Allowed purchase time slots
3. ✅ **Procurement Options** - Supplier options for each item code with:
   - Pricing
   - Lead times
   - Discounts
   - Payment terms
4. ✅ **Budget Data** - Budget limits for each time period

## Current System Status

The system already has **sample data** seeded:
- ✅ Sample projects (PROJ001, PROJ002)
- ✅ Sample project items
- ✅ Sample procurement options
- ✅ Sample budget data

## How to Run Optimization

### Step 1: Access the Optimization Page

As **admin** user, you should be able to view the optimization page:
- Navigate to: **Optimization** from the sidebar

### Step 2: Check User Role

The "Run Optimization" button is only visible to users with the **finance** role. Since you're logged in as **admin**, you have two options:

**Option A: Login as Finance User**
1. Logout
2. Login with:
   - Username: `finance1`
   - Password: `finance123`
3. Navigate to **Optimization** page
4. Click **"Run Optimization"** button

**Option B: Update Admin Role**
We can modify the code to allow admins to run optimizations too.

### Step 3: Configure Optimization Parameters

When you click "Run Optimization", you'll see a dialog with:

- **Maximum Time Slots**: Default 12 periods
- **Time Limit (seconds)**: Default 300 seconds (5 minutes)

These are good defaults for testing.

### Step 4: Run and View Results

1. Click **"Run Optimization"**
2. Wait for the optimization to complete (usually 5-30 seconds)
3. View the results showing:
   - Total optimized cost
   - Number of items optimized
   - Execution time
   - Detailed purchase schedule

## Understanding the Results

### Optimization Status

- **OPTIMAL**: Best possible solution found
- **FEASIBLE**: Valid solution found (may not be the absolute best)
- **INFEASIBLE**: No solution exists (budget too tight, constraints impossible)

### Results Table

Each row shows:
- **Project**: Which project the item belongs to
- **Item Code**: The item being purchased
- **Purchase Time**: When to buy (time period)
- **Delivery Time**: When it will be delivered
- **Quantity**: How much to buy
- **Cost**: Total cost for this purchase

### Cost Savings

The optimization automatically considers:
- ✅ Bulk purchase discounts
- ✅ Payment term advantages (cash vs credit)
- ✅ Budget distribution across periods
- ✅ Just-in-time delivery to minimize holding costs

## Quick Start: Enable Admin Access

Let me update the code to allow admin users to run optimizations:


