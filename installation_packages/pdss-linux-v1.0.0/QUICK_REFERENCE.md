# 🚀 PDSS v1.0.0 - Quick Reference

## 📦 **Installation Package**

**Version**: 1.0.0  
**Build**: 202510220030  
**Platform**: Linux (Ubuntu/Debian/CentOS)  
**Status**: ✅ **PRODUCTION READY**

---

## ⚡ **QUICK START**

### **1. Install:**
```bash
unzip pdss-linux-v1.0.0-202510220030.zip
cd pdss-linux-v1.0.0
chmod +x install.sh
sudo ./install.sh
```

### **2. Start:**
```bash
sudo ./start.sh
```

### **3. Access:**
- **URL**: `http://your-server-ip:3000`
- **Login**: `admin` / `admin123`
- **⚠️ Change password immediately!**

---

## 👥 **DEFAULT USERS**

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | Admin |
| `pmo_user` | `pmo123` | PMO |
| `pm1` | `pm123` | PM |
| `procurement1` | `procurement123` | Procurement |
| `finance1` | `finance123` | Finance |

---

## 🎯 **COMPLETE WORKFLOW**

### **Step 1: Create Project (PMO)**
- Login as PMO
- Navigate to Projects
- Create new project

### **Step 2: Add Items (PM)**
- Login as PM
- Navigate to project
- Add project items
- Add delivery options (dates in future!)

### **Step 3: Finalize Items (PMO)**
- Login as PMO
- Navigate to project items
- Click "Finalize Item" for each

### **Step 4: Add Procurement Options (Procurement)**
- Login as Procurement
- Navigate to Procurement page
- For each item: Add 3-5 supplier options
- Link to delivery options
- Can mark as finalized during creation

### **Step 5: Run Optimization (Finance)**
- Login as Finance
- Navigate to Advanced Optimization
- Run optimization
- Review proposals

### **Step 6: Save & Finalize (Finance)**
- Select best proposal
- Click "Save Proposal"
- Navigate to Finalized Decisions
- Finalize decisions (PROPOSED → LOCKED)

### **Step 7: Track Execution (Procurement/Finance)**
- Navigate to Procurement Plan
- Confirm deliveries
- Enter invoices
- Track payments

---

## 🔧 **MANAGEMENT COMMANDS**

### **Start Platform:**
```bash
sudo ./start.sh
```

### **Stop Platform:**
```bash
sudo ./stop.sh
```

### **Check Status:**
```bash
sudo docker-compose ps
```

### **View Logs:**
```bash
sudo docker-compose logs -f
```

### **Restart Services:**
```bash
sudo docker-compose restart
```

---

## 📊 **KEY FEATURES**

- ✅ Multi-project management
- ✅ Multi-currency support (IRR, USD, EUR)
- ✅ Advanced optimization (5 strategies)
- ✅ Role-based access control
- ✅ Invoice & payment tracking
- ✅ Responsive design (mobile/tablet/desktop)
- ✅ Real-time updates
- ✅ Complete audit trail

---

## 🐛 **TROUBLESHOOTING**

### **Cannot Access Platform:**
```bash
# Check if containers are running
sudo docker-compose ps

# Restart services
sudo docker-compose restart

# Check firewall
sudo ufw allow 3000
```

### **Login Issues:**
```bash
# Reset admin password
sudo docker-compose exec backend python /app/reset_admin_password.py
```

### **Database Issues:**
```bash
# Access database
sudo docker-compose exec postgres psql -U postgres -d procurement_dss

# Check tables
\dt

# Check users
SELECT username, role FROM users;
```

---

## 📚 **DOCUMENTATION**

- **Complete Guide**: `INSTALLATION_GUIDE.md`
- **User Manual**: `docs/USER_GUIDE.md`
- **Admin Guide**: `docs/ADMIN_GUIDE.md`
- **API Docs**: `docs/API_DOCUMENTATION.md`
- **All Guides**: `docs/` folder (30+ files)

---

## ⚠️ **IMPORTANT NOTES**

1. **Delivery Dates**: Must be in the FUTURE for optimization to work
2. **Change Passwords**: Change all default passwords after installation
3. **Finalize Items**: Items must be finalized by PMO before appearing in procurement
4. **Optimization**: Requires finalized items with delivery options and procurement options
5. **Revert**: Cannot revert completed transactions (delivered + invoiced + paid)

---

## 🎉 **READY TO USE!**

For detailed instructions, see `INSTALLATION_GUIDE.md`  
For help, check documentation in `docs/` folder

**Version 1.0.0 - Production Ready** ✅
