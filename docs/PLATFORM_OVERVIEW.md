# 🏢 Procurement Decision Support System (PDSS)

## Platform Overview

The **Procurement Decision Support System (PDSS)** is an enterprise-grade platform designed to streamline and optimize the procurement process across project-based organizations. Built with modern technologies and following best practices, PDSS provides a comprehensive solution for managing procurement decisions, tracking financial data, and optimizing procurement strategies.

---

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Key Features](#key-features)
3. [Architecture](#architecture)
4. [User Roles & Permissions](#user-roles--permissions)
5. [Workflow](#workflow)
6. [Modules](#modules)
7. [Technology Stack](#technology-stack)
8. [System Requirements](#system-requirements)
9. [Getting Started](#getting-started)
10. [Support & Documentation](#support--documentation)

---

## 🎯 Introduction

PDSS was developed to address the complex challenges of procurement management in project-driven organizations. The platform enables organizations to:

- **Centralize** procurement data and decisions
- **Optimize** supplier selection and cost analysis
- **Track** financial obligations and cash flow
- **Analyze** procurement patterns and performance
- **Automate** decision-making processes
- **Collaborate** across different departments

### Problem Statement

Traditional procurement processes often suffer from:
- Fragmented data across multiple systems
- Manual decision-making without data-driven insights
- Lack of visibility into financial commitments
- Inefficient communication between departments
- Difficulty in tracking procurement performance

### Solution

PDSS provides an integrated platform that:
- ✅ Centralizes all procurement-related data
- ✅ Provides advanced analytics and optimization
- ✅ Enables role-based access and workflows
- ✅ Tracks complete procurement lifecycle
- ✅ Generates actionable insights and reports

---

## 🌟 Key Features

### 1. **Project Management**
- Create and manage multiple projects
- Track project budgets and timelines
- Organize items by project
- Monitor project procurement status

### 2. **Item Management**
- Master items catalog with specifications
- Project-specific item management
- Delivery options tracking
- Item finalization workflow

### 3. **Procurement Management**
- Multi-supplier comparison
- Currency management with exchange rates
- Payment terms configuration
- Bundle discount tracking
- Lead time analysis

### 4. **Financial Tracking**
- Invoice management
- Payment tracking
- Cash flow forecasting
- Expected vs actual cash-in dates
- Multi-currency support

### 5. **Decision Optimization**
- Multi-criteria decision analysis
- Weight-based scoring system
- Pareto front analysis
- What-if scenario planning
- Automated recommendations

### 6. **Analytics & Reporting**
- Real-time dashboards
- Procurement performance metrics
- Supplier performance tracking
- Cost analysis and forecasting
- Custom reports generation

### 7. **User Management**
- Role-based access control (RBAC)
- Multiple user roles (Admin, PMO, PM, Procurement, Finance)
- Secure authentication
- Activity tracking

### 8. **Workflow Management**
- Item finalization workflow (PMO/Admin → Procurement)
- Status tracking across lifecycle
- Approval workflows
- Notification system

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Frontend Layer                         │
│  React + TypeScript + Material-UI + Recharts                │
│  (Port 3000)                                                 │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST API
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                       Backend Layer                          │
│  FastAPI + Python 3.11 + SQLAlchemy + Pydantic             │
│  (Port 8000)                                                 │
└────────────────────┬────────────────────────────────────────┘
                     │ SQL Queries
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      Database Layer                          │
│  PostgreSQL 15 + PostGIS                                    │
│  (Port 5432)                                                 │
└─────────────────────────────────────────────────────────────┘
```

### Component Architecture

```
Frontend (React)
├── Pages
│   ├── Authentication (Login)
│   ├── Dashboard
│   ├── Projects Management
│   ├── Items Management
│   ├── Procurement Management
│   ├── Finance Tracking
│   ├── Optimization Engine
│   ├── Analytics & Reports
│   └── User Management
├── Components
│   ├── Layout (Sidebar, AppBar)
│   ├── Data Tables
│   ├── Charts & Visualizations
│   ├── Forms & Dialogs
│   └── Shared Components
├── Services
│   ├── API Client
│   ├── Authentication
│   └── Data Management
└── Context
    ├── AuthContext
    └── Theme Management

Backend (FastAPI)
├── Routes (API Endpoints)
│   ├── /auth (Authentication)
│   ├── /users (User Management)
│   ├── /projects (Projects)
│   ├── /items (Project Items)
│   ├── /items-master (Items Catalog)
│   ├── /procurement (Procurement Options)
│   ├── /decisions (Finalized Decisions)
│   ├── /finance (Financial Tracking)
│   ├── /optimization (Decision Optimization)
│   ├── /analytics (Analytics & Reports)
│   └── /currencies (Currency Management)
├── Models (Database ORM)
│   ├── User
│   ├── Project
│   ├── ProjectItem
│   ├── ItemMaster
│   ├── ProcurementOption
│   ├── Decision
│   ├── Currency
│   └── ExchangeRate
├── Schemas (Pydantic Validation)
├── CRUD Operations
├── Authentication & Authorization
└── Business Logic

Database (PostgreSQL)
├── Tables
│   ├── users
│   ├── projects
│   ├── project_items
│   ├── items_master
│   ├── procurement_options
│   ├── decisions
│   ├── currencies
│   ├── exchange_rates
│   └── delivery_options
├── Indexes (Performance)
├── Foreign Keys (Relationships)
└── Constraints (Data Integrity)
```

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Containers                         │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Frontend   │  │   Backend    │  │  PostgreSQL  │     │
│  │  (Node.js)   │  │  (Python)    │  │  (Database)  │     │
│  │  Port 3000   │  │  Port 8000   │  │  Port 5432   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                    Docker Network                           │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
              Docker Compose Orchestration
```

---

## 👥 User Roles & Permissions

### Role Hierarchy

| Role | Level | Description |
|------|-------|-------------|
| **Admin** | 5 | Full system access, user management, configuration |
| **PMO** | 4 | Project Management Office - oversight and finalization |
| **PM** | 3 | Project Manager - project execution and item management |
| **Procurement** | 2 | Procurement team - supplier management and options |
| **Finance** | 2 | Finance team - financial tracking and analytics |

### Permissions Matrix

| Feature | Admin | PMO | PM | Procurement | Finance |
|---------|:-----:|:---:|:--:|:-----------:|:-------:|
| **Dashboard** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Projects** | | | | | |
| - View Projects | ✅ | ✅ | ✅ | ❌ | ✅ |
| - Create/Edit Projects | ✅ | ✅ | ✅ | ❌ | ❌ |
| - Delete Projects | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Project Items** | | | | | |
| - View Items | ✅ | ✅ | ✅ | ❌ | ✅ |
| - Create/Edit Items | ✅ | ✅ | ✅ | ❌ | ❌ |
| - Delete Items | ✅ | ✅ | ✅ | ❌ | ❌ |
| - Finalize Items | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Procurement** | | | | | |
| - View Finalized Items | ✅ | ✅ | ✅ | ✅ | ✅ |
| - Create Options | ✅ | ❌ | ❌ | ✅ | ❌ |
| - Edit Options | ✅ | ❌ | ❌ | ✅ | ❌ |
| - Delete Options | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Finance** | | | | | |
| - View Financial Data | ✅ | ❌ | ❌ | ❌ | ✅ |
| - Update Payments | ✅ | ❌ | ❌ | ❌ | ✅ |
| - View Cash Flow | ✅ | ❌ | ❌ | ❌ | ✅ |
| **Optimization** | | | | | |
| - Run Optimization | ✅ | ❌ | ❌ | ❌ | ✅ |
| - View Results | ✅ | ❌ | ❌ | ❌ | ✅ |
| - Finalize Decisions | ✅ | ❌ | ❌ | ❌ | ✅ |
| **Analytics** | | | | | |
| - View Analytics | ✅ | ✅ | ✅ | ❌ | ✅ |
| - Generate Reports | ✅ | ✅ | ✅ | ❌ | ✅ |
| - Export Data | ✅ | ✅ | ✅ | ❌ | ✅ |
| **User Management** | | | | | |
| - View Users | ✅ | ❌ | ❌ | ❌ | ❌ |
| - Create Users | ✅ | ❌ | ❌ | ❌ | ❌ |
| - Edit Users | ✅ | ❌ | ❌ | ❌ | ❌ |
| - Delete Users | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Configuration** | | | | | |
| - Manage Weights | ✅ | ❌ | ❌ | ❌ | ❌ |
| - Manage Currencies | ✅ | ❌ | ❌ | ✅ | ✅ |
| - Items Master | ✅ | ✅ | ✅ | ❌ | ✅ |

---

## 🔄 Workflow

### Complete Procurement Workflow

```
1. PROJECT CREATION (PM/PMO)
   ↓
2. ADD PROJECT ITEMS (PM/PMO)
   - Add items from master catalog or create new
   - Define quantities and delivery options
   - Attach specifications and documents
   ↓
3. ITEM FINALIZATION (PMO/Admin)
   - Review project items
   - Finalize items ready for procurement
   - Items now visible to procurement team
   ↓
4. PROCUREMENT OPTIONS (Procurement Team)
   - View finalized items
   - Create supplier options for each item
   - Define pricing, lead times, payment terms
   - Add bundle discounts
   ↓
5. DECISION OPTIMIZATION (Finance/Admin)
   - Run optimization algorithms
   - Analyze Pareto fronts
   - Review recommendations
   - Perform what-if analysis
   ↓
6. DECISION FINALIZATION (Finance/Admin)
   - Select optimal procurement options
   - Lock decisions
   - Generate procurement plan
   ↓
7. FINANCIAL TRACKING (Finance)
   - Track invoices and payments
   - Monitor cash flow
   - Update actual dates
   - Reconcile accounts
   ↓
8. ANALYTICS & REPORTING (All Roles)
   - View dashboards
   - Generate reports
   - Analyze performance
   - Export data
```

### Item Lifecycle

```
[PENDING] → [SUGGESTED] → [DECIDED] → [PROCURED] → [FULFILLED] → [PAID] → [CASH_RECEIVED]
   │            │             │            │             │           │            │
   PM/PMO      PMO        Finance     Procurement    Procurement  Finance     Finance
```

---

## 📦 Modules

### 1. Dashboard Module
**Purpose:** Centralized view of key metrics and system status

**Features:**
- Real-time KPIs
- Quick access to recent projects
- Procurement status overview
- Financial summary
- Alerts and notifications

**Accessible by:** All roles

---

### 2. Projects Module
**Purpose:** Manage projects and associated items

**Features:**
- Create/Edit/Delete projects
- Project budget tracking
- Project timeline management
- Item listing by project
- Project status tracking

**Accessible by:** Admin, PMO, PM, Finance

---

### 3. Project Items Module
**Purpose:** Manage items within projects

**Features:**
- Add items from master catalog
- Create custom project items
- Define delivery options
- Upload specifications
- Track item status
- **Finalize items** (PMO/Admin only)

**Accessible by:** Admin, PMO, PM, Finance (view)

**Key Feature: Item Finalization**
- PMO/Admin can finalize items when ready for procurement
- Finalized items become visible in Procurement module
- Creates controlled workflow gate

---

### 4. Items Master Module
**Purpose:** Centralized catalog of all items

**Features:**
- Company-specific item database
- Item specifications and models
- Item categorization
- Auto-generated item codes
- Searchable catalog

**Accessible by:** Admin, PMO, PM, Finance

---

### 5. Procurement Module
**Purpose:** Manage supplier options for finalized items

**Features:**
- View only finalized items (controlled access)
- Create supplier options
- Multi-currency pricing
- Payment terms configuration
- Bundle discount management
- Lead time tracking
- Delivery options management

**Accessible by:** Admin, Procurement, Finance (view)

**Workflow:**
1. View finalized items from projects
2. For each item, create multiple supplier options
3. Define pricing and terms
4. Options become available for optimization

---

### 6. Procurement Plan Module
**Purpose:** View and manage procurement execution plan

**Features:**
- Timeline view of procurement activities
- Item-by-item procurement status
- Supplier assignments
- Delivery scheduling
- Progress tracking

**Accessible by:** Admin, Procurement, PM, PMO, Finance

---

### 7. Finance Module
**Purpose:** Financial tracking and cash flow management

**Features:**
- Invoice tracking
- Payment scheduling
- Cash flow forecasting
- Expected vs actual dates
- Payment status tracking
- Multi-currency aggregation

**Accessible by:** Admin, Finance

---

### 8. Optimization Module
**Purpose:** Decision analysis and optimization

**Features:**
- Multi-criteria optimization
- Pareto front visualization
- What-if scenario analysis
- Cost-benefit analysis
- Lead time optimization
- Risk assessment

**Accessible by:** Admin, Finance

**Optimization Criteria:**
- Total Cost
- Lead Time
- Supplier Reliability
- Payment Terms
- Quality Score

---

### 9. Finalized Decisions Module
**Purpose:** Track and manage finalized procurement decisions

**Features:**
- View all finalized decisions
- Decision history
- Rationale tracking
- Performance monitoring
- Decision reversals (with audit trail)

**Accessible by:** Admin, Finance

---

### 10. Analytics Module
**Purpose:** Business intelligence and insights

**Features:**
- Procurement performance dashboards
- Supplier performance analysis
- Cost trend analysis
- Budget variance analysis
- Forecasting models
- Custom visualizations

**Accessible by:** Admin, PMO, PM, Finance

---

### 11. Reports Module
**Purpose:** Generate and export reports

**Features:**
- Pre-built report templates
- Custom report builder
- Export to Excel/PDF
- Scheduled reports
- Email distribution

**Accessible by:** Admin, PMO, PM, Finance

---

### 12. User Management Module
**Purpose:** Manage system users and permissions

**Features:**
- User CRUD operations
- Role assignment
- Password management
- Active/Inactive status
- User activity logs

**Accessible by:** Admin only

---

### 13. Decision Weights Module
**Purpose:** Configure optimization criteria weights

**Features:**
- Set importance weights for criteria
- View current configuration
- Reset to defaults
- Weight validation

**Accessible by:** Admin only

---

### 14. Currency Management Module
**Purpose:** Manage currencies and exchange rates

**Features:**
- Add/Edit currencies
- Set base currency
- Update exchange rates
- Historical rate tracking
- Automatic rate updates (optional)

**Accessible by:** Admin, Procurement, Finance

---

## 💻 Technology Stack

### Frontend
- **Framework:** React 18.x
- **Language:** TypeScript 4.x
- **UI Library:** Material-UI (MUI) 5.x
- **Charts:** Recharts 2.x
- **State Management:** React Context API
- **Routing:** React Router 6.x
- **HTTP Client:** Axios
- **Date Handling:** date-fns
- **Build Tool:** Create React App
- **Package Manager:** npm

### Backend
- **Framework:** FastAPI 0.109.x
- **Language:** Python 3.11
- **ORM:** SQLAlchemy 2.x (Async)
- **Validation:** Pydantic 2.x
- **Authentication:** JWT (python-jose)
- **Password Hashing:** passlib + bcrypt
- **Database Driver:** asyncpg
- **CORS:** FastAPI CORS middleware
- **API Documentation:** Swagger UI / ReDoc (auto-generated)

### Database
- **RDBMS:** PostgreSQL 15
- **Extensions:** PostGIS (spatial data)
- **Connection Pooling:** SQLAlchemy async engine
- **Migrations:** SQL scripts (manual)

### DevOps & Deployment
- **Containerization:** Docker 24.x
- **Orchestration:** Docker Compose 2.x
- **Web Server:** Uvicorn (ASGI)
- **Proxy Server:** Nginx (optional, for production)
- **Process Manager:** systemd (Linux)

### Development Tools
- **Version Control:** Git
- **Code Editor:** VS Code (recommended)
- **API Testing:** Postman / cURL
- **Database Tool:** pgAdmin / DBeaver

---

## 🖥️ System Requirements

### Minimum Requirements (Development)
- **OS:** Windows 10/11, Linux (Ubuntu 20.04+), macOS 11+
- **CPU:** 2 cores, 2.0 GHz
- **RAM:** 4 GB
- **Storage:** 5 GB free space
- **Docker:** Docker 20.x+, Docker Compose 2.x+

### Recommended Requirements (Production)
- **OS:** Linux (Ubuntu 22.04 LTS recommended)
- **CPU:** 4+ cores, 3.0 GHz
- **RAM:** 8+ GB
- **Storage:** 50+ GB SSD
- **Network:** 100 Mbps+ connection
- **Docker:** Docker 24.x+, Docker Compose 2.x+

### Browser Compatibility
- **Chrome:** 90+
- **Firefox:** 88+
- **Safari:** 14+
- **Edge:** 90+

---

## 🚀 Getting Started

### Quick Start (Development)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cahs_flow_project
   ```

2. **Start the platform**
   ```bash
   # Windows
   start.bat

   # Linux/Mac
   ./start.sh
   ```

3. **Access the platform**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

4. **Default Login**
   - Username: `admin`
   - Password: ⚠️ **Change on first login!**

### Installation Methods

1. **Docker Compose** (Recommended)
   - Easiest setup
   - Isolated environment
   - Cross-platform

2. **Linux Package** (Production)
   - Automated installer
   - Systemd integration
   - Auto-start on boot

3. **Windows Package** (Production)
   - Batch script installer
   - Windows Task Scheduler
   - Service management

For detailed installation instructions, see:
- [Linux Installation Guide](./LINUX_INSTALLATION.md)
- [Windows Installation Guide](./WINDOWS_INSTALLATION.md)
- [Docker Installation Guide](./DOCKER_INSTALLATION.md)

---

## 📚 Support & Documentation

### Documentation Structure

```
docs/
├── PLATFORM_OVERVIEW.md (This file)
├── USER_GUIDE.md
├── ADMIN_GUIDE.md
├── API_DOCUMENTATION.md
├── INSTALLATION/
│   ├── LINUX_INSTALLATION.md
│   ├── WINDOWS_INSTALLATION.md
│   └── DOCKER_INSTALLATION.md
├── CONFIGURATION/
│   ├── ENVIRONMENT_VARIABLES.md
│   ├── DATABASE_SETUP.md
│   └── SECURITY.md
├── FEATURES/
│   ├── PROJECT_MANAGEMENT.md
│   ├── PROCUREMENT_WORKFLOW.md
│   ├── OPTIMIZATION_ENGINE.md
│   └── ANALYTICS.md
└── TROUBLESHOOTING/
    ├── COMMON_ISSUES.md
    ├── FAQ.md
    └── DEBUGGING.md
```

### Getting Help

- **Documentation:** Check the `docs/` folder
- **API Reference:** http://localhost:8000/docs
- **Issue Tracker:** <repository-issues-url>
- **Email Support:** <support-email>

---

## 🔐 Security Features

- ✅ JWT-based authentication
- ✅ Password hashing (bcrypt)
- ✅ Role-based access control (RBAC)
- ✅ SQL injection prevention (ORM)
- ✅ XSS protection
- ✅ CORS configuration
- ✅ Secure session management
- ✅ Activity logging
- ✅ Data validation (Pydantic)

---

## 📊 Performance & Scalability

### Performance Optimizations
- Database indexing on frequently queried columns
- Async I/O operations (FastAPI + SQLAlchemy)
- Connection pooling
- Lazy loading of relationships
- Frontend code splitting
- Caching strategies

### Scalability Considerations
- Horizontal scaling via Docker replicas
- Database read replicas (future)
- CDN for static assets (future)
- Load balancing (future)

---

## 🔄 Backup & Recovery

### Backup Strategy
- **Database:** Daily automated backups
- **Files:** Document and specification backups
- **Configuration:** Environment and settings backup
- **Retention:** 30 days recommended

### Recovery Procedures
- Automated restore scripts provided
- Point-in-time recovery support
- Disaster recovery procedures documented

---

## 📝 Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2025-10-20 | Initial release with core features |
| - | - | - Logo integration |
| - | - | - Item finalization workflow |
| - | - | - Procurement process improvements |
| - | - | - Enhanced error handling |

---

## 🎯 Roadmap

### Planned Features (Future Versions)

**v1.1.0**
- Email notifications
- Advanced reporting
- Audit log viewer
- Bulk operations

**v1.2.0**
- Mobile responsive design
- REST API versioning
- Webhook support
- Integration APIs

**v2.0.0**
- AI-powered recommendations
- Predictive analytics
- Supplier rating system
- Blockchain integration (optional)

---

## 🤝 Contributing

We welcome contributions! Please see:
- [CONTRIBUTING.md](./CONTRIBUTING.md)
- [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)
- [DEVELOPMENT.md](./DEVELOPMENT.md)

---

## 📄 License

[Specify your license here]

---

## 🙏 Acknowledgments

- **InoTech** - Platform development and branding
- **FastAPI** - Modern Python web framework
- **React** - Frontend library
- **PostgreSQL** - Reliable database system
- **Material-UI** - Beautiful UI components

---

## 📞 Contact

- **Website:** <website-url>
- **Email:** <contact-email>
- **Support:** <support-email>
- **Documentation:** <docs-url>

---

**Built with ❤️ by InoTech**

*Last Updated: October 20, 2025*

