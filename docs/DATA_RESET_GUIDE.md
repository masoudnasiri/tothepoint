# 🔄 PDSS Data Reset and Reseed Guide

## Overview

This guide explains how to wipe existing operational data and reseed the database with fresh test data that includes **both USD and Iranian Rial (IRR)** pricing.

---

## ⚠️ Important Warnings

**Before You Begin:**
- ✅ This will DELETE all operational data
- ✅ Admin user credentials will be preserved
- ✅ Database structure remains intact
- ✅ All other users will be recreated with default passwords
- ❌ **Backup your data first if needed!**

---

## 🆕 New Data Structure

### Currencies
- **USD (US Dollar)** - Base currency
- **IRR (Iranian Rial)** - Exchange rate: 1 USD = 42,000 IRR

### Projects (3 Total)
1. **IT Infrastructure Upgrade 2025** ($250,000)
2. **Office Equipment Procurement** ($150,000)
3. **Data Center Expansion** ($500,000)

### Items Master Catalog (15 Items)
- **Dell**: Laptops, Desktops, Servers, Monitors
- **HP**: Laptops, Desktops, Servers, Printers
- **Lenovo**: Laptops, Desktops
- **Cisco**: Switches, Routers
- **Synology**: NAS Storage
- **Western Digital**: Enterprise HDDs
- **APC**: UPS Systems

### Project Items (13 Items - All Finalized)
- Ready for procurement immediately
- Realistic quantities and delivery dates
- Complete specifications

### Procurement Options (~30+ Options)
- **Mixed Pricing**: Some in USD, some in IRR
- **Multiple Suppliers** per item
- **Realistic Costs**: Based on current market prices
- **Varied Lead Times**: 7-50 days
- **Bundle Discounts**: Available for bulk orders
- **Payment Terms**: Cash or installments

---

## 🚀 How to Reset Data

### Method 1: Windows (Recommended)

1. **Stop the Application** (if running)
   ```batch
   docker-compose down
   ```

2. **Run Reset Script**
   ```batch
   reset_data.bat
   ```

3. **Follow Prompts**
   - Script will ask for confirmation
   - Type `YES` to confirm
   - Wait for completion

4. **Restart Backend**
   ```batch
   docker-compose up -d backend
   ```

5. **Restart Frontend**
   ```batch
   docker-compose up -d frontend
   ```

---

### Method 2: Linux/Mac

1. **Stop the Application** (if running)
   ```bash
   docker-compose down
   ```

2. **Make Script Executable**
   ```bash
   chmod +x reset_data.sh
   ```

3. **Run Reset Script**
   ```bash
   ./reset_data.sh
   ```

4. **Follow Prompts**
   - Script will ask for confirmation
   - Type `YES` to confirm
   - Wait for completion

5. **Restart Backend**
   ```bash
   docker-compose up -d backend
   ```

6. **Restart Frontend**
   ```bash
   docker-compose up -d frontend
   ```

---

### Method 3: Docker (Alternative)

If running in Docker environment:

```bash
# Stop containers
docker-compose down

# Run reset script inside container
docker-compose run --rm backend python reset_and_reseed_data.py

# Restart all
docker-compose up -d
```

---

## 📊 What Gets Created

### Users (6 Total)

| Username | Password | Role | Access |
|----------|----------|------|--------|
| admin | admin123 | Admin | Full system access |
| pmo_user | pmo123 | PMO | Project oversight, finalization |
| pm1 | pm123 | PM | Project management |
| pm2 | pm123 | PM | Project management |
| procurement1 | proc123 | Procurement | Supplier management |
| finance1 | finance123 | Finance | Financial tracking, optimization |

### Currency Data

**USD (Base Currency)**
- Code: USD
- Symbol: $
- Decimal Places: 2
- Base: Yes

**Iranian Rial**
- Code: IRR
- Symbol: ﷼
- Decimal Places: 0
- Exchange Rate: 42,000 IRR = 1 USD

### Sample Item Pricing

**Example: Dell Latitude 5540 Laptop**
- Supplier 1: $1,200 (USD) - Dell Direct USA
- Supplier 2: 52,000,000 IRR - Local IT Distributor
- Supplier 3: $1,150 (USD) - Import Specialist

**Example: HP ProLiant DL380 Gen11 Server**
- Supplier 1: $15,000 (USD) - HP Enterprise
- Supplier 2: 650,000,000 IRR - Data Center Equipment Iran

**Example: Cisco Catalyst 9300 Switch**
- Supplier 1: $12,000 (USD) - Cisco Authorized
- Supplier 2: 520,000,000 IRR - Network Equipment Co

---

## ✅ Verification Steps

After reset, verify the data:

### 1. Check Currencies

```sql
SELECT * FROM currencies;
```

Expected: 2 currencies (USD and IRR)

### 2. Check Exchange Rates

```sql
SELECT c.code, er.rate 
FROM exchange_rates er
JOIN currencies c ON c.id = er.currency_id;
```

Expected: 1 USD = 42,000 IRR

### 3. Check Projects

```sql
SELECT name, budget FROM projects;
```

Expected: 3 projects

### 4. Check Finalized Items

```sql
SELECT COUNT(*) FROM project_items WHERE is_finalized = true;
```

Expected: 13 finalized items

### 5. Check Procurement Options

```sql
SELECT 
    po.supplier_name,
    po.base_cost,
    c.code as currency
FROM procurement_options po
JOIN currencies c ON c.id = po.currency_id
LIMIT 10;
```

Expected: Mix of USD and IRR options

---

## 🎯 Testing the New Data

### Test 1: Login as Different Roles

1. **Login as PMO**
   - Username: `pmo_user`
   - Password: `pmo123`
   - Verify: Can see all projects

2. **Login as Procurement**
   - Username: `procurement1`
   - Password: `proc123`
   - Navigate to Procurement module
   - Verify: 13 finalized items visible

3. **Login as Finance**
   - Username: `finance1`
   - Password: `finance123`
   - Navigate to Finance module
   - Verify: Can see all data

### Test 2: View Mixed Currency Pricing

1. Go to **Procurement** module
2. Expand any item
3. Verify you see:
   - Some options in **USD ($)**
   - Some options in **IRR (﷼)**
   - Costs displayed in original currency

### Test 3: Run Optimization

1. Login as Finance or Admin
2. Navigate to **Advanced Optimization**
3. Select an item with mixed currency options
4. Run optimization
5. Verify: System handles both currencies correctly

### Test 4: Create New Procurement Option

1. Login as Procurement
2. Select an item
3. Create new option
4. Choose currency: USD or IRR
5. Enter appropriate cost
6. Save and verify

---

## 🔧 Troubleshooting

### Issue: "Module not found" Error

**Solution:**
```bash
# Install required Python packages
pip install asyncio sqlalchemy asyncpg passlib bcrypt
```

### Issue: Database Connection Error

**Solution:**
1. Verify database is running:
   ```bash
   docker-compose ps postgres
   ```

2. Check database URL in script matches your setup

3. Update DATABASE_URL if needed:
   ```python
   DATABASE_URL = "postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/procurement_dss"
   ```

### Issue: "Permission Denied" on Linux/Mac

**Solution:**
```bash
chmod +x reset_data.sh
```

### Issue: Script Hangs

**Solution:**
1. Press Ctrl+C to cancel
2. Check if database is locked:
   ```bash
   docker-compose restart postgres
   ```
3. Try again

### Issue: Incomplete Data After Reset

**Solution:**
1. Run reset again:
   ```bash
   docker-compose down
   python backend/reset_and_reseed_data.py
   docker-compose up -d
   ```

---

## 📋 What Gets Deleted

The reset script deletes:
- ✅ All projects
- ✅ All project items
- ✅ All procurement options
- ✅ All decisions
- ✅ All delivery options
- ✅ All items master entries
- ✅ All currencies and exchange rates
- ✅ All users (except admin)

The reset script preserves:
- ✅ Database structure (tables, columns, constraints)
- ✅ Admin user account
- ✅ System configuration

---

## 💾 Backup Before Reset (Optional)

If you want to keep your current data:

### Quick Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres procurement_dss > backup_before_reset.sql

# Or use the backup script
docker-compose exec postgres pg_dump -U postgres procurement_dss | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Restore from Backup

```bash
# If you need to restore
docker-compose exec -T postgres psql -U postgres procurement_dss < backup_before_reset.sql
```

---

## 🎓 Understanding the New Data

### Currency Conversion

The system automatically handles currency conversion:

**Example:**
- Option 1: $1,200 USD
- Option 2: 52,000,000 IRR
- Exchange Rate: 42,000 IRR/USD

**Comparison (in base currency USD):**
- Option 1: $1,200
- Option 2: $1,238 (52,000,000 / 42,000)

### Realistic Pricing

All prices are based on approximate current market rates:

**Budget Range Items:**
- Laptops: $1,100 - $1,300 (or 46M - 56M IRR)
- Desktops: $800 - $1,200 (or 34M - 52M IRR)
- Monitors: $400 - $500 (or 17M - 21M IRR)

**Enterprise Items:**
- Servers: $8,000 - $15,000 (or 336M - 630M IRR)
- Network Switches: $10,000 - $12,000 (or 420M - 504M IRR)
- Storage Systems: $3,000 - $4,000 (or 126M - 168M IRR)

---

## 🚀 Next Steps After Reset

1. **Change Default Passwords**
   - Login as admin
   - Update all user passwords
   - Especially admin password!

2. **Configure Exchange Rates**
   - Update IRR exchange rate if needed
   - Navigate to Currency Management
   - Update rates regularly

3. **Review Projects**
   - Check project details
   - Adjust budgets if needed
   - Update timelines

4. **Test Procurement Workflow**
   - Login as different roles
   - Complete full workflow
   - Verify everything works

5. **Train Users**
   - Show mixed currency features
   - Explain new data structure
   - Demonstrate procurement process

---

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review error messages carefully
3. Check Docker logs: `docker-compose logs backend`
4. Verify database connection
5. Contact system administrator

---

## 📝 Script Details

**Location:** `backend/reset_and_reseed_data.py`

**What it does:**
1. Connects to database
2. Deletes operational data (preserves structure)
3. Creates currencies (USD, IRR)
4. Creates exchange rates
5. Creates users with hashed passwords
6. Creates items master catalog
7. Creates projects
8. Creates project items (all finalized)
9. Creates procurement options (mixed USD/IRR)
10. Displays summary

**Safety Features:**
- Requires confirmation (type `YES`)
- Shows what will be deleted
- Displays summary after completion
- Preserves admin user
- Maintains database integrity

---

**Ready to reset? Run the script and follow the prompts!**

*Last Updated: October 20, 2025*

