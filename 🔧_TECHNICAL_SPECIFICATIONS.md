# 🔧 Technical Specifications
## Procurement Decision Support System - Technical Overview

---

## 📋 **System Architecture**

### **Architecture Pattern:** Microservices with Docker Compose

```
┌──────────────────────────────────────────────────────┐
│                   FRONTEND (React)                    │
│  React 18 + TypeScript + Material-UI + Axios         │
│  Port: 3000 (Nginx)                                  │
└─────────────────────┬────────────────────────────────┘
                      │ REST API (HTTPS)
┌─────────────────────▼────────────────────────────────┐
│              BACKEND (FastAPI)                        │
│  Python 3.9+ + FastAPI + SQLAlchemy + Pydantic      │
│  Port: 8000 (Uvicorn ASGI)                          │
└─────────────────────┬────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼────────┐         ┌────────▼──────────┐
│ OPTIMIZATION   │         │  DATABASE         │
│ OR-Tools       │         │  PostgreSQL 13    │
│ NetworkX       │         │  Port: 5432       │
│ 4 Solvers      │         │  Volume: 20GB+    │
└────────────────┘         └───────────────────┘
```

---

## 💻 **Technology Stack**

### **Backend:**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | FastAPI | 0.100+ | REST API server |
| **Language** | Python | 3.9+ | Core application |
| **Database ORM** | SQLAlchemy | 2.0+ | Database abstraction |
| **Database Driver** | asyncpg | 0.27+ | Async PostgreSQL driver |
| **Validation** | Pydantic | 2.0+ | Data validation & serialization |
| **Authentication** | JWT | - | Token-based auth |
| **Password Hashing** | bcrypt | - | Secure password storage |
| **Optimization** | OR-Tools | 9.7+ | AI optimization engine |
| **Graph Analysis** | NetworkX | 3.1+ | Dependency analysis |
| **ASGI Server** | Uvicorn | 0.23+ | Production server |

### **Frontend:**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | React | 18.2+ | UI framework |
| **Language** | TypeScript | 5.0+ | Type-safe development |
| **UI Library** | Material-UI | 5.14+ | Component library |
| **HTTP Client** | Axios | 1.4+ | API communication |
| **Routing** | React Router | 6.14+ | Client-side routing |
| **State Management** | React Context | - | Global state |
| **Charts** | Chart.js/Recharts | - | Data visualization |
| **Date Handling** | date-fns | 2.30+ | Date utilities |
| **Build Tool** | Create React App | 5.0+ | Build & bundling |

### **Database:**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **DBMS** | PostgreSQL | 13+ | Primary data store |
| **Data Types** | JSONB, Numeric, Timestamp | - | Flexible schemas |
| **Indexing** | B-tree, GiST | - | Query optimization |
| **Persistence** | Docker Volume | - | Data durability |

### **Infrastructure:**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Containerization** | Docker | 20.10+ | Application packaging |
| **Orchestration** | Docker Compose | 2.0+ | Multi-container management |
| **Web Server** | Nginx | 1.21+ | Reverse proxy (optional) |
| **Process Manager** | Uvicorn | - | Python ASGI server |

---

## 🗄️ **Database Schema**

### **Core Tables:**

```sql
users (id, username, password_hash, role, created_at)
  ↓ (assignments)
projects (id, project_code, name, status, start_date, end_date)
  ↓ (items)
project_items (id, project_id, item_code, quantity, delivery_dates)
  ↓ (options)
procurement_options (id, item_code, supplier, price, quality, payment_terms)
  ↓ (decisions)
finalized_decisions (id, project_item_id, option_id, status, bunch_id)
  ↓ (cashflow)
cashflow_events (id, decision_id, event_type, amount, date, is_cancelled)

budget_data (id, budget_date, available_budget)
optimization_runs (id, run_uuid, strategy, status, results_json)
project_assignments (user_id, project_id, assigned_at)
delivery_options (id, project_item_id, delivery_date, delivery_slot)
```

### **Relationships:**
- Users ↔ Projects (Many-to-Many via assignments)
- Projects ↔ Items (One-to-Many)
- Items ↔ Procurement Options (One-to-Many via item_code)
- Items ↔ Finalized Decisions (One-to-Many)
- Decisions ↔ Cashflow Events (One-to-Many)

---

## 🔐 **Security Features**

### **Authentication:**
- **JWT Tokens:** Secure, stateless authentication
- **Password Hashing:** bcrypt with salt (cost factor: 12)
- **Token Expiration:** Configurable (default: 24 hours)
- **Secure Headers:** CORS, CSP, HSTS

### **Authorization:**
- **Role-Based Access Control (RBAC):** 5 roles
- **Endpoint Protection:** Dependency injection guards
- **Resource Isolation:** Users see only permitted data
- **Permission Matrix:** Granular access control

### **Data Protection:**
- **SQL Injection:** Parameterized queries (SQLAlchemy)
- **XSS:** React auto-escaping
- **CSRF:** Token-based protection
- **Input Validation:** Pydantic schemas on all endpoints
- **Output Sanitization:** Type-safe responses

### **Audit Trail:**
- **User Actions:** Who, what, when logging
- **Decision History:** Complete lifecycle tracking
- **Database Triggers:** Automatic timestamp updates
- **Immutable Records:** Decision history preservation

---

## 📊 **Performance Specifications**

### **Response Times (95th percentile):**
| Endpoint | Response Time | Notes |
|----------|--------------|-------|
| Authentication | < 200ms | JWT generation |
| List Operations | < 100ms | With pagination |
| Single Resource | < 50ms | By ID lookup |
| Create/Update | < 150ms | With validation |
| Dashboard Load | < 500ms | Complex aggregations |
| Optimization (100 items) | < 30 sec | CP-SAT solver |
| Optimization (1000 items) | < 300 sec | Configurable timeout |
| Excel Export | < 2 sec | 1000 rows |

### **Throughput:**
| Operation | Requests/Second | Concurrent Users |
|-----------|----------------|------------------|
| Read Operations | 2,000 | 500+ |
| Write Operations | 500 | 100+ |
| Authentication | 1,000 | - |
| Optimization | 10 (concurrent) | 50+ queued |

### **Scalability:**
| Resource | Limit | Notes |
|----------|-------|-------|
| Concurrent Users | 1,000+ | With load balancing |
| Projects | Unlimited | Database capacity |
| Items per Project | 10,000+ | Optimization depends on solver |
| Procurement Options | 100,000+ | Per item |
| Database Size | 1TB+ | PostgreSQL limit: 32TB |
| Historical Data | 5+ years | Recommended archival: 2 years |

---

## 🖥️ **System Requirements**

### **Production Server (Small - Up to 100 users):**
```
CPU: 4 cores (Intel Xeon or AMD EPYC)
RAM: 8 GB
Storage: 50 GB SSD
Network: 100 Mbps
OS: Ubuntu 20.04 LTS / CentOS 8 / RHEL 8
```

### **Production Server (Medium - Up to 500 users):**
```
CPU: 8 cores
RAM: 16 GB
Storage: 200 GB SSD
Network: 1 Gbps
OS: Ubuntu 20.04 LTS
Database: Separate PostgreSQL server recommended
```

### **Production Server (Large - 1000+ users):**
```
Application Server:
  CPU: 16 cores
  RAM: 32 GB
  Storage: 100 GB SSD

Database Server:
  CPU: 8 cores
  RAM: 32 GB
  Storage: 500 GB SSD (RAID 10)

Load Balancer:
  Nginx/HAProxy
  2+ application server instances
  
Cache Layer (Optional):
  Redis 6.2+
  4 GB RAM
```

### **Development Environment:**
```
CPU: 2 cores
RAM: 4 GB
Storage: 20 GB
OS: Windows 10+, macOS 11+, Linux
Docker: 20.10+
```

---

## 🔌 **API Specifications**

### **REST API:**
- **Protocol:** HTTP/1.1, HTTP/2
- **Format:** JSON
- **Authentication:** Bearer Token (JWT)
- **Versioning:** URL-based (v1)
- **Rate Limiting:** 1000 req/hour per user (configurable)
- **Pagination:** Offset-based (skip, limit)
- **Filtering:** Query parameters
- **Sorting:** Query parameters (order_by)

### **OpenAPI/Swagger:**
- **Documentation:** Auto-generated from FastAPI
- **Endpoint:** `/docs` (Swagger UI)
- **Endpoint:** `/redoc` (ReDoc UI)
- **Schema:** `/openapi.json`

### **Key Endpoints:**
```
Authentication:
  POST   /token                    # Login
  GET    /users/me                 # Current user

Projects:
  GET    /projects/                # List projects
  POST   /projects/                # Create project
  GET    /projects/{id}            # Get project
  PUT    /projects/{id}            # Update project
  DELETE /projects/{id}            # Delete project

Optimization:
  POST   /optimization/run         # Run optimization
  GET    /optimization/runs        # List runs
  GET    /optimization/runs/{uuid} # Get results

Dashboard:
  GET    /dashboard/cashflow       # Cashflow analysis
  GET    /dashboard/summary        # Dashboard summary

Finance:
  GET    /finance/budget           # List budgets
  POST   /finance/budget           # Create budget
  
Decisions:
  GET    /decisions/finalized      # List decisions
  POST   /decisions/finalize       # Finalize decisions
  PUT    /decisions/{id}/status    # Update decision status
```

---

## 🐳 **Docker Configuration**

### **Services:**
```yaml
services:
  postgres:
    image: postgres:13
    ports: 5432
    volumes: postgres_data:/var/lib/postgresql/data
    
  backend:
    build: ./backend
    ports: 8000
    depends_on: [postgres]
    environment:
      - DATABASE_URL=postgresql://...
      
  frontend:
    build: ./frontend
    ports: 3000
    depends_on: [backend]
    environment:
      - REACT_APP_API_URL=/api
```

### **Volumes:**
```
postgres_data:  # Persistent database storage
  driver: local
  size: 20GB+ (grows with data)
```

### **Resource Limits:**
```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
      reservations:
        cpus: '1'
        memory: 2G
```

---

## 📦 **Deployment Options**

### **1. Docker Compose (Recommended for Quick Start)**
```powershell
docker-compose up -d
# Single command deployment
# All services configured
# Development and production ready
```

### **2. Kubernetes (Enterprise Scale)**
```yaml
Deployment:
  - Frontend (React): 3+ replicas
  - Backend (FastAPI): 5+ replicas
  - PostgreSQL: StatefulSet with persistent volume
  - Ingress: Nginx ingress controller
  - HPA: Horizontal Pod Autoscaler
```

### **3. Cloud Platforms:**

**AWS:**
- ECS/Fargate: Container hosting
- RDS PostgreSQL: Managed database
- ALB: Load balancing
- CloudFront: CDN
- S3: Static assets

**Azure:**
- Container Instances: Container hosting
- Azure Database for PostgreSQL: Managed DB
- Application Gateway: Load balancing
- CDN: Content delivery

**Google Cloud:**
- Cloud Run: Serverless containers
- Cloud SQL: Managed PostgreSQL
- Cloud Load Balancing
- Cloud CDN

---

## 🔗 **Integration Capabilities**

### **REST API Integration:**
```python
# Example: External system integration
import requests

# Authenticate
response = requests.post(
    'https://your-platform.com/token',
    data={'username': 'api_user', 'password': 'secret'}
)
token = response.json()['access_token']

# Get projects
projects = requests.get(
    'https://your-platform.com/projects/',
    headers={'Authorization': f'Bearer {token}'}
).json()
```

### **Webhook Support (Optional Feature):**
```json
{
  "event": "decision.finalized",
  "timestamp": "2025-01-10T12:00:00Z",
  "data": {
    "decision_id": 123,
    "project_id": 45,
    "item_code": "ITEM-001",
    "total_cost": 50000
  }
}
```

### **Data Export Formats:**
- ✅ Excel (.xlsx)
- ✅ CSV
- ✅ JSON (REST API)
- ✅ SQL dumps

### **Data Import Formats:**
- ✅ Excel (.xlsx)
- ✅ CSV
- ✅ JSON (REST API)

---

## 📈 **Monitoring & Logging**

### **Application Logs:**
```
Location: docker logs <container_name>
Level: INFO, WARNING, ERROR, DEBUG
Format: Structured JSON logs
Rotation: Daily, 7-day retention
```

### **Database Logs:**
```
Location: PostgreSQL logs
Queries: Slow query log (> 1s)
Connections: Connection pool monitoring
```

### **Health Checks:**
```
GET /health       # Application health
GET /db/health    # Database connectivity
```

### **Metrics (Optional - Prometheus):**
```
# Request count
http_requests_total{method="GET", endpoint="/projects/"}

# Request duration
http_request_duration_seconds{endpoint="/optimization/run"}

# Active users
active_users_gauge

# Database connections
db_connections_active
```

---

## 🔄 **Backup & Recovery**

### **Automated Backup:**
```powershell
# Backup script (backup_database.bat)
docker-compose exec postgres pg_dump \
  -U postgres procurement_dss > backup_$(date).sql
```

### **Restore:**
```powershell
# Restore script (restore_database.bat)
docker-compose exec -T postgres psql \
  -U postgres procurement_dss < backup.sql
```

### **Backup Strategy:**
- **Frequency:** Daily automated backups
- **Retention:** 30 days
- **Storage:** External volume/S3
- **Testing:** Monthly restore tests

---

## 🛡️ **Disaster Recovery**

### **RTO (Recovery Time Objective):** 2 hours
### **RPO (Recovery Point Objective):** 24 hours

### **Recovery Steps:**
1. Deploy clean Docker environment
2. Restore database from backup
3. Restart services
4. Verify data integrity
5. Resume operations

---

## 🔧 **Maintenance**

### **Updates:**
- **Backend:** Docker image rebuild
- **Frontend:** Docker image rebuild
- **Database:** PostgreSQL minor version updates (safe)
- **Dependencies:** `pip install --upgrade` / `npm update`

### **Downtime:**
- **Planned:** 30 minutes/month (optional updates)
- **Unplanned:** < 1 hour/year (99.9% uptime target)

---

## 📊 **Technical Support**

### **System Requirements Check:**
```powershell
# Run health check
.\check-system.bat

# Outputs:
# ✅ Docker running
# ✅ Containers healthy
# ✅ Database connected
# ✅ OR-Tools installed
# ✅ Solvers available
```

### **Troubleshooting:**
- Comprehensive documentation (50+ guides)
- Error code reference
- Common issues & solutions
- Docker logs analysis

---

## ✅ **Compliance & Standards**

### **Standards:**
- ✅ REST API best practices
- ✅ OpenAPI 3.0 specification
- ✅ OAuth 2.0 / JWT authentication
- ✅ OWASP security guidelines
- ✅ GDPR data protection ready
- ✅ ISO 27001 security controls

### **Code Quality:**
- ✅ TypeScript strict mode
- ✅ Python type hints
- ✅ Linting (ESLint, Pylint)
- ✅ Code formatting (Prettier, Black)
- ✅ API documentation (auto-generated)

---

## 🎯 **Technical Advantages**

### **vs. Monolithic Applications:**
- ✅ Microservices architecture (scalable)
- ✅ Container-based deployment (portable)
- ✅ Async I/O (high throughput)
- ✅ Type-safe (TypeScript + Pydantic)

### **vs. Legacy Systems:**
- ✅ Modern tech stack (React, FastAPI)
- ✅ Cloud-native (Docker, K8s)
- ✅ RESTful API (integration-ready)
- ✅ Responsive UI (mobile-friendly)

---

## 🚀 **Getting Started (IT Team)**

### **Prerequisites:**
```bash
# Required
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM, 2 CPU cores
- 20GB free disk space

# Optional (for development)
- Node.js 16+ (frontend dev)
- Python 3.9+ (backend dev)
- PostgreSQL client (database access)
```

### **Quick Deploy:**
```powershell
# Clone repository
git clone https://github.com/masoudnasiri/tothepoint.git
cd tothepoint

# Start services
docker-compose up -d

# Verify health
.\check-system.bat

# Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### **Environment Configuration:**
```env
# .env file
DATABASE_URL=postgresql://user:pass@postgres:5432/db
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

---

**Repository:** https://github.com/masoudnasiri/tothepoint  
**Documentation:** 50+ technical guides included  
**Support:** Available for enterprise deployments

---

*Production-Ready • Scalable • Secure • Well-Documented*

