# 🏢 Procurement Decision Support System (DSS)

**Enterprise-Level Project Procurement & Financial Optimization Platform**

[![Status](https://img.shields.io/badge/Status-Production%20Ready-success)]()
[![Version](https://img.shields.io/badge/Version-1.0.0-blue)]()
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED)]()

---

## 🚀 Quick Start

### **For First-Time Users:**
```bash
# 1. Start the system
.\start.bat

# 2. Access the application
http://localhost:3000

# 3. Default credentials
Username: admin
Password: admin123
```

### **For Developers:**
```bash
# Start with Docker
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

---

## 📚 Documentation

**All documentation has been organized in the `/docs` folder.**

### **Essential Documents:**

📖 **[Start Here](docs/README_START_HERE.md)** - Complete system overview

🚀 **[Quick Start Guide](docs/QUICK_START_WINDOWS.md)** - Get up and running fast

📚 **[Documentation Index](docs/📚_DOCUMENTATION_INDEX.md)** - Complete documentation catalog

👤 **[User Guide](docs/USER_GUIDE.md)** - End-user manual

🔧 **[Setup Guide](docs/SETUP.md)** - Detailed installation instructions

---

## ✨ Key Features

### **📊 Reports & Analytics**
- Comprehensive financial dashboards
- EVM (Earned Value Management) analytics
- Risk forecasting and analysis
- Supplier performance scorecards

### **🎯 Advanced Optimization**
- Multi-objective optimization engine
- Budget and timeline constraints
- Custom strategy support
- OR-Tools powered solver

### **📦 Procurement Management**
- Delivery tracking and confirmation
- Invoice management
- Multi-proposal comparison
- Supplier management

### **💰 Financial Control**
- Dual cashflow tracking (planned vs actual)
- Budget variance analysis
- Payment installment schedules
- Cost forecasting

### **📈 Portfolio Analytics**
- Project health monitoring
- Risk-based highlighting
- Real-time KPI tracking
- Executive dashboards

### **🗂️ Items Master Catalog**
- Centralized item database
- File attachments support
- Reusable item definitions
- Category management

---

## 🛠️ Technology Stack

### **Backend:**
- FastAPI (Python)
- PostgreSQL
- SQLAlchemy ORM
- OR-Tools (Google)

### **Frontend:**
- React + TypeScript
- Material-UI
- Recharts
- Axios

### **Infrastructure:**
- Docker & Docker Compose
- Nginx (reverse proxy)
- Multi-stage builds

---

## 👥 User Roles

| Role | Description | Access Level |
|------|-------------|--------------|
| **Admin** | System administrator | Full access |
| **PMO** | Portfolio Management Office | All projects |
| **PM** | Project Manager | Assigned projects only |
| **Procurement** | Procurement team | Procurement & delivery |
| **Finance** | Finance team | Financial data & optimization |

---

## 📁 Project Structure

```
cahs_flow_project/
├── backend/           # FastAPI backend
│   ├── app/          # Application code
│   └── requirements.txt
├── frontend/          # React frontend
│   ├── src/          # Source code
│   └── package.json
├── docs/             # 📚 All documentation (170+ files)
├── docker-compose.yml
├── start.bat         # Windows start script
├── stop.bat          # Windows stop script
└── README.md         # This file
```

---

## 🎯 Common Tasks

### **Start/Stop System:**
```bash
.\start.bat          # Start all services
.\stop.bat           # Stop all services
.\check-system.bat   # Check system status
```

### **View Logs:**
```bash
.\logs.bat           # View all logs
docker-compose logs backend -f    # Backend logs only
docker-compose logs frontend -f   # Frontend logs only
```

### **Reset System:**
```bash
.\reset.bat          # Full system reset (WARNING: Deletes data!)
```

---

## 📊 System URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Main application |
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Database** | localhost:5432 | PostgreSQL |

---

## 🔧 Configuration

### **Environment Variables:**
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret key
- `ALLOWED_ORIGINS` - CORS allowed origins

### **Default Ports:**
- Frontend: 3000
- Backend: 8000
- Database: 5432

---

## 📦 Installation Package

Pre-built installation packages are available in the `installation_packages/` folder for easy deployment on Windows and Linux systems.

See: [docs/✅_DEPLOYMENT_PACKAGE_COMPLETE.md](docs/✅_DEPLOYMENT_PACKAGE_COMPLETE.md)

---

## 🆘 Troubleshooting

### **Common Issues:**

**Problem:** Services won't start
```bash
# Solution: Check if ports are in use
netstat -ano | findstr :3000
netstat -ano | findstr :8000
```

**Problem:** Database connection error
```bash
# Solution: Restart database
docker-compose restart postgres
```

**Problem:** Frontend not loading
```bash
# Solution: Rebuild frontend
docker-compose up -d --build frontend
```

For more troubleshooting, see: [docs/COMPLETE_TESTING_GUIDE.md](docs/COMPLETE_TESTING_GUIDE.md)

---

## 📖 Learn More

### **Feature Documentation:**
- [Reports & Analytics](docs/✅_REPORTS_ANALYTICS_FEATURE_COMPLETE.md)
- [Procurement Plan](docs/PROCUREMENT_PLAN_FEATURE_COMPLETE.md)
- [Items Master](docs/🎊_ITEMS_MASTER_COMPLETE.md)
- [Optimization Engine](docs/OPTIMIZATION_GUIDE.md)
- [Invoice Management](docs/INVOICE_IMPLEMENTATION_COMPLETE.md)

### **Technical Documentation:**
- [Project Structure](docs/PROJECT_STRUCTURE.md)
- [OR-Tools Architecture](docs/OR_TOOLS_ARCHITECTURE.md)
- [Technical Specifications](docs/🔧_TECHNICAL_SPECIFICATIONS.md)

### **User Guides:**
- [Complete User Guide](docs/USER_GUIDE.md)
- [PM User Permissions](docs/PM_USER_PERMISSIONS.md)
- [PMO Role Guide](docs/👥_PMO_ROLE_COMPLETE.md)

---

## 🎓 Training & Support

### **Getting Started:**
1. Read the [Quick Start Guide](docs/QUICK_START_WINDOWS.md)
2. Review the [User Guide](docs/USER_GUIDE.md)
3. Explore the [Documentation Index](docs/📚_DOCUMENTATION_INDEX.md)

### **Video Tutorials:**
Coming soon!

### **Support:**
- Check documentation in `/docs` folder
- Review troubleshooting guides
- Contact system administrator

---

## 🔒 Security

- JWT-based authentication
- Role-based access control (RBAC)
- Secure password hashing
- CORS protection
- SQL injection prevention

---

## 📈 Performance

- Optimized database queries
- Caching strategies
- Lazy loading
- Pagination support
- Docker multi-stage builds

---

## 🌟 Highlights

✅ **Production Ready** - Fully tested and deployed  
✅ **Enterprise Grade** - Built for large-scale operations  
✅ **User Friendly** - Intuitive interface and workflows  
✅ **Highly Configurable** - Flexible to your needs  
✅ **Well Documented** - 170+ documentation files  
✅ **Docker Enabled** - Easy deployment anywhere  

---

## 📝 License

Proprietary - All rights reserved

---

## 👏 Credits

Developed with ❤️ for enterprise procurement management

---

## 📞 Contact

For questions, issues, or feature requests, please contact your system administrator.

---

**Version:** 1.0.0  
**Last Updated:** October 10, 2025  
**Status:** ✅ Production Ready

---

### **🚀 Ready to get started?**

1. Run `.\start.bat`
2. Open http://localhost:3000
3. Login with admin/admin123
4. Explore the features!

**Happy optimizing! 📊✨**

