# 👤 PDSS User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Login & Authentication](#login--authentication)
3. [Dashboard Overview](#dashboard-overview)
4. [Working with Projects](#working-with-projects)
5. [Managing Project Items](#managing-project-items)
6. [Procurement Process](#procurement-process)
7. [Financial Tracking](#financial-tracking)
8. [Analytics & Reports](#analytics--reports)
9. [User Settings](#user-settings)
10. [Best Practices](#best-practices)

---

## Getting Started

### First Time Login

1. Open your web browser and navigate to: `http://localhost:3000`
2. You will see the PDSS login page with the InoTech logo
3. Enter your credentials (provided by your administrator)
4. ⚠️ **Important:** Change your password on first login!

### Navigation

The platform uses a sidebar menu for navigation:
- **Dashboard** - Overview of system status
- **Analytics & Forecast** - Performance metrics and predictions
- **Reports & Analytics** - Generate custom reports
- **Projects** - Manage projects and items
- **Procurement** - View finalized items and create options
- **Procurement Plan** - Execution timeline
- **Finance** - Financial tracking (Finance role only)
- **Advanced Optimization** - Decision optimization (Admin/Finance only)
- **Finalized Decisions** - Historical decisions (Admin/Finance only)
- **Users** - User management (Admin only)
- **Decision Weights** - Configure optimization (Admin only)
- **Items Master** - Central item catalog

---

## Login & Authentication

### Login Process

1. Enter your **username** (case-sensitive)
2. Enter your **password**
3. Click **Sign In**

### Changing Your Password

1. Click on your profile icon (top-right)
2. Navigate to **Users** page
3. Find your user account
4. Click **Edit**
5. Enter your new password
6. Click **Save**

### Password Requirements

- Minimum 6 characters
- Mix of letters and numbers recommended
- Avoid common passwords

### Logout

1. Click on your profile icon (top-right)
2. Click **Logout**

---

## Dashboard Overview

The dashboard provides a quick overview of:

### Key Metrics
- Total number of projects
- Active procurement items
- Financial summary
- Recent activities

### Quick Actions
- Create new project
- View recent items
- Access reports
- Check notifications

---

## Working with Projects

### Creating a Project

**Role Required:** Admin, PMO, PM

1. Navigate to **Projects** from sidebar
2. Click **Add Project** button
3. Fill in project details:
   - **Project Name** (required)
   - **Budget** (optional)
   - **Start Date** (optional)
   - **End Date** (optional)
   - **Description** (optional)
4. Click **Create**

### Viewing Projects

- All your accessible projects are listed in a table
- Use the search box to filter projects
- Click on a project name to view details

### Editing a Project

1. Find the project in the list
2. Click the **Edit** icon (pencil)
3. Modify the fields
4. Click **Save**

### Deleting a Project

⚠️ **Warning:** This action cannot be undone!

1. Find the project in the list
2. Click the **Delete** icon (trash)
3. Confirm the deletion

---

## Managing Project Items

### Viewing Project Items

1. Go to **Projects** page
2. Click **View Items** button for a project
3. You'll see all items for that project

### Adding Items from Master Catalog

**Recommended Method:**

1. Click **Add from Master** button
2. Browse or search the items catalog
3. Select the company and item
4. Define:
   - **Quantity** (required)
   - **Delivery Options** - Add one or more dates
   - **External Purchase** - Check if purchased externally
   - **Description** - Project-specific notes
5. Click **Add to Project**

### Creating Custom Items

**For items not in catalog:**

1. Click **Add Item** button
2. Enter manually:
   - **Item Code** (required)
   - **Item Name** (optional)
   - **Quantity** (required)
   - **Delivery Options** (required)
   - **External Purchase** (optional)
   - **Description** (optional)
3. Click **Create**

### Managing Delivery Options

Delivery options represent possible delivery dates for an item:

1. **Adding Delivery Dates:**
   - Use the date picker
   - Click **Add Date**
   - Multiple dates can be added

2. **Removing Delivery Dates:**
   - Click the **X** next to the date

### Item Status Lifecycle

Items progress through statuses:
- **PENDING** - Initial state
- **SUGGESTED** - Option suggested
- **DECIDED** - Decision made
- **PROCURED** - Procurement initiated
- **FULFILLED** - Item delivered
- **PAID** - Payment completed
- **CASH_RECEIVED** - Cash flow completed

### Finalizing Items (PMO/Admin Only)

**This is a critical step in the workflow!**

1. Review the project items
2. For items ready for procurement, click the **Finalize** button (✅ icon)
3. Confirm the finalization
4. Item will show **FINALIZED** status
5. Item becomes visible to Procurement team

**Important:** Only finalized items appear in the Procurement module!

---

## Procurement Process

### Accessing Procurement Module

**Role Required:** Admin, Procurement, Finance (view only)

1. Navigate to **Procurement** from sidebar
2. You will see only **finalized items** from projects
3. Items are grouped by item code

### Creating Procurement Options

**Role Required:** Admin, Procurement

For each finalized item, create supplier options:

1. Click on an item code to expand
2. Click **Add Option** button
3. Fill in supplier details:

**Basic Information:**
- **Supplier Name** (required)
- **Base Cost** (required)
- **Currency** (required - select from dropdown)

**Delivery & Lead Time:**
- **Lead Time** (days)
- **Delivery Date** (select from available dates)

**Discounts:**
- **Bundle Threshold** - Minimum quantity for discount
- **Bundle Discount %** - Discount percentage

**Payment Terms:**
- **Cash** - Immediate payment with optional discount
- **Installments** - Define payment schedule

4. Click **Create**

### Viewing Procurement Options

- All options for an item are listed in a table
- Compare suppliers side-by-side
- View calculated totals with discounts

### Editing Procurement Options

1. Find the option in the list
2. Click **Edit** icon
3. Modify fields
4. Click **Save**

### Finalize Procurement Options

When a supplier option is ready:
1. Click **Finalize** button for the option
2. Confirm finalization
3. Option is locked and ready for optimization

---

## Financial Tracking

**Role Required:** Admin, Finance

### Tracking Invoices and Payments

1. Navigate to **Finance** module
2. View all finalized procurement decisions
3. Track dates:
   - **Decision Date**
   - **Procurement Date**
   - **Payment Date**
   - **Invoice Submission Date**
   - **Expected Cash In Date**
   - **Actual Cash In Date**

### Updating Payment Information

1. Find the item in the Finance table
2. Click **Edit** icon
3. Update the relevant dates
4. Click **Save**

### Cash Flow Monitoring

- View total expected cash outflows
- Track actual vs expected dates
- Monitor payment status
- Generate financial reports

---

## Analytics & Reports

### Accessing Analytics

**Role Required:** Admin, PMO, PM, Finance

1. Navigate to **Analytics & Forecast** from sidebar
2. View interactive dashboards

### Available Analytics

**Procurement Performance:**
- Items by status
- Procurement timeline
- Supplier performance
- Cost breakdown

**Financial Analytics:**
- Cash flow forecast
- Budget vs actual
- Payment trends
- Currency exposure

**Project Analytics:**
- Project progress
- Item completion rates
- Delivery schedule adherence

### Generating Reports

1. Navigate to **Reports & Analytics**
2. Select report type
3. Choose filters (date range, project, etc.)
4. Click **Generate**
5. Export to Excel or PDF

---

## User Settings

### Updating Your Profile

1. Click profile icon (top-right)
2. Select profile option
3. Update your information
4. Click **Save**

### Changing Password

See [Login & Authentication](#login--authentication) section above.

---

## Best Practices

### Project Management

✅ **DO:**
- Create projects before adding items
- Use clear, descriptive project names
- Keep project budgets updated
- Add meaningful descriptions

❌ **DON'T:**
- Delete projects with active items
- Leave project fields incomplete
- Create duplicate projects

### Item Management

✅ **DO:**
- Use the Master Catalog when possible
- Add multiple delivery options for flexibility
- Include project-specific descriptions
- Finalize items only when fully ready

❌ **DON'T:**
- Create custom items for catalog items
- Finalize items prematurely
- Skip delivery option dates
- Leave descriptions empty

### Procurement

✅ **DO:**
- Create multiple supplier options for comparison
- Include accurate lead times
- Define clear payment terms
- Update bundle discounts

❌ **DON'T:**
- Create options for non-finalized items
- Leave cost fields empty
- Skip currency selection
- Forget to finalize options

### Financial Tracking

✅ **DO:**
- Update payment dates promptly
- Track both expected and actual dates
- Reconcile cash flow regularly
- Generate periodic reports

❌ **DON'T:**
- Ignore date discrepancies
- Wait too long to update
- Skip invoice tracking
- Forget actual cash in dates

---

## Common Tasks Quick Reference

| Task | Steps | Role |
|------|-------|------|
| **Create Project** | Projects → Add Project → Fill Form → Create | PM/PMO |
| **Add Item** | Project → View Items → Add Item → Fill Form | PM/PMO |
| **Finalize Item** | Project Items → Click ✅ Icon → Confirm | PMO/Admin |
| **Create Procurement Option** | Procurement → Select Item → Add Option | Procurement |
| **Run Optimization** | Optimization → Select Items → Run Analysis | Finance/Admin |
| **Update Payment** | Finance → Find Item → Edit → Update Dates | Finance |
| **Generate Report** | Reports → Select Type → Filter → Generate | All |

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + K` | Quick search |
| `Esc` | Close dialog |
| `Enter` | Submit form |
| `Tab` | Navigate fields |

---

## Getting Help

If you need assistance:

1. **Check this User Guide** - Most questions answered here
2. **Contact your administrator** - For access issues
3. **Check the FAQ** - Common questions documented
4. **Submit a support ticket** - For technical issues

---

## Troubleshooting

### Can't see finalized items in Procurement
- **Solution:** Ensure items are finalized by PMO/Admin first

### Can't create procurement options
- **Solution:** Check that you have Procurement role assigned

### Missing menu items
- **Solution:** Contact admin to verify your role permissions

### Data not saving
- **Solution:** Check internet connection and try again

---

**For more detailed information, see:**
- [Admin Guide](./ADMIN_GUIDE.md)
- [API Documentation](./API_DOCUMENTATION.md)
- [Troubleshooting Guide](./troubleshooting/COMMON_ISSUES.md)

---

*Last Updated: October 20, 2025*

