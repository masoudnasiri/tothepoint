# Procurement DSS - Technical Architecture Documentation

## 🏗️ **Platform Overview**

The **Procurement Decision Support System (DSS)** is a comprehensive enterprise-level platform for project procurement planning, financial optimization, and delivery tracking. It provides role-based access control, advanced optimization algorithms, and comprehensive analytics for procurement decision-making.

---

## 🎯 **Core Business Flows**

### **1. Project Lifecycle Management**
```
Project Creation → Phase Definition → Item Planning → Procurement → Delivery → Payment
```

### **2. Procurement Optimization Flow**
```
Item Requirements → Procurement Options → Optimization Engine → Decision Finalization → Execution
```

### **3. Financial Management Flow**
```
Budget Planning → Cost Optimization → Payment Tracking → Cash Flow Analysis → Reporting
```

### **4. Delivery Tracking Flow**
```
Order Confirmation → Delivery Confirmation → PM Acceptance → Invoice Processing → Payment
```

---

## 🗄️ **Database Architecture**

### **Core Entities & Relationships**

#### **1. User Management**
- **Users**: Role-based access (Admin, PMO, PM, Procurement, Finance)
- **Project Assignments**: Many-to-many relationship between users and projects

#### **2. Project Management**
- **Projects**: Core project entities with phases and items
- **Project Phases**: Milestone-based project structure
- **Project Items**: Items required for each project with quantities and specifications

#### **3. Item Management**
- **Items Master**: Central catalog of all available items
- **Project Items**: Project-specific item requirements
- **Procurement Options**: Available suppliers and pricing for each item

#### **4. Decision Management**
- **Finalized Decisions**: Locked procurement decisions
- **Optimization Results**: AI-generated optimization proposals
- **Decision Reversions**: Ability to revert and re-optimize decisions

#### **5. Financial Management**
- **Budget Data**: Project budget allocations by time period
- **Cashflow Events**: Actual and forecasted financial transactions
- **Payment Tracking**: Payment schedules and actual payments

#### **6. Delivery Management**
- **Delivery Options**: Available delivery dates and methods
- **Delivery Tracking**: Status tracking from order to delivery
- **Invoice Management**: Invoice processing and payment tracking

---

## 🔌 **API Architecture**

### **Authentication & Authorization**
```
/auth/
├── POST /login          # User authentication
├── POST /register       # User registration (admin only)
└── GET /me             # Current user info
```

### **User Management**
```
/users/
├── GET /                # List all users
├── POST /               # Create user (admin only)
├── GET /{user_id}      # Get user details
├── PUT /{user_id}      # Update user
├── DELETE /{user_id}    # Delete user
└── POST /{user_id}/assign-project  # Assign user to project
```

### **Project Management**
```
/projects/
├── GET /                # List projects (role-filtered)
├── POST /               # Create project (PMO only)
├── GET /{project_id}   # Get project details
├── PUT /{project_id}    # Update project
├── DELETE /{project_id} # Delete project
└── GET /{project_id}/items  # Get project items
```

### **Item Management**
```
/items-master/
├── GET /                # List all items
├── POST /               # Create item
├── GET /{item_id}       # Get item details
├── PUT /{item_id}       # Update item
└── DELETE /{item_id}    # Delete item

/items/
├── GET /project/{project_id}  # Get project items
├── POST /                     # Create project item
├── GET /{item_id}             # Get item details
├── PUT /{item_id}             # Update item
└── DELETE /{item_id}          # Delete item
```

### **Procurement Management**
```
/procurement/
├── GET /options         # List procurement options
├── POST /options        # Create procurement option
├── GET /options/{id}    # Get option details
├── PUT /options/{id}    # Update option
├── DELETE /options/{id} # Delete option
└── GET /item-codes      # Get available item codes
```

### **Optimization Engine**
```
/finance/
├── POST /optimize              # Run CP-SAT optimization
├── POST /optimize-enhanced     # Run advanced optimization
├── GET /optimization-results  # Get optimization results
└── GET /dashboard             # Finance dashboard
```

### **Decision Management**
```
/decisions/
├── GET /                # List decisions
├── POST /save-proposal  # Save optimization proposal
├── POST /finalize       # Finalize decisions
├── POST /revert         # Revert decisions
└── GET /{decision_id}   # Get decision details
```

### **Procurement Plan & Delivery Tracking**
```
/procurement-plan/
├── GET /                # List procurement items
├── GET /{item_id}       # Get item details
├── POST /{item_id}/confirm-delivery    # Confirm delivery (Procurement)
├── POST /{item_id}/accept-delivery    # Accept delivery (PM)
├── POST /{item_id}/enter-invoice     # Enter invoice data
└── GET /export         # Export to Excel
```

### **Analytics & Reporting**
```
/analytics/
├── GET /project/{project_id}/evm      # Earned Value Management
├── GET /project/{project_id}/cashflow-forecast  # Cash flow forecast
├── GET /portfolio/cashflow-forecast   # Portfolio cash flow
└── GET /project/{project_id}/risk-analysis     # Risk analysis

/reports/
├── GET /                # Comprehensive reports data
├── GET /export/excel   # Export reports to Excel
├── GET /filters/projects    # Get filter options
├── GET /filters/suppliers  # Get supplier options
└── GET /data-summary       # Data summary statistics
```

### **Dashboard & Monitoring**
```
/dashboard/
├── GET /cashflow       # Cash flow analysis
├── GET /cashflow/export # Export cash flow
└── GET /summary        # Dashboard summary
```

---

## 🧠 **Optimization Engine**

### **Solver Types**
1. **CP-SAT (Constraint Programming)**: Best for complex constraints
2. **GLOP (Linear Programming)**: Fast for large-scale problems
3. **SCIP (Mixed-Integer Programming)**: Balance between CP and LP
4. **CBC (Coin-or Branch and Cut)**: Alternative MIP solver

### **Optimization Strategies**
1. **LOWEST_COST**: Minimize total procurement cost
2. **PRIORITY_WEIGHTED**: Weight decisions by project priority
3. **FAST_DELIVERY**: Minimize delivery time
4. **SMOOTH_CASHFLOW**: Balance cash flow across periods
5. **BALANCED**: Balance all factors

### **Constraints**
- Budget limitations per time period
- Delivery date requirements
- Supplier capacity constraints
- Project priority weighting
- Cash flow smoothing

---

## 🔐 **Role-Based Access Control (RBAC)**

### **User Roles & Permissions**

#### **Admin**
- Full system access
- User management
- System configuration
- All financial operations

#### **PMO (Project Management Office)**
- Project creation and management
- User assignment to projects
- Portfolio-level analytics
- Cross-project optimization

#### **PM (Project Manager)**
- Assigned projects only
- Project item management
- Delivery acceptance
- Project-specific analytics
- Read-only financial data

#### **Procurement Team**
- Procurement option management
- Delivery confirmation
- Invoice processing
- Supplier management
- Full financial visibility

#### **Finance**
- Budget management
- Optimization execution
- Financial analytics
- Payment processing
- Cost analysis

---

## 📊 **Analytics & Reporting**

### **Financial Analytics**
- **Cash Flow Analysis**: Inflow/outflow projections
- **Budget vs Actual**: Cost variance analysis
- **Earned Value Management (EVM)**: PV, EV, AC, CPI, SPI
- **Cost Performance**: Variance analysis and forecasting

### **Operational Analytics**
- **Supplier Performance**: On-time delivery, cost variance
- **Procurement Cycle Time**: Time from decision to delivery
- **Risk Analysis**: Delay forecasts and risk assessment
- **Portfolio Analytics**: Cross-project optimization

### **Report Types**
1. **Financial Summary**: Budget vs actuals, cash flow
2. **EVM Analytics**: Earned value management metrics
3. **Risk & Forecasts**: Delay predictions, risk items
4. **Operational Performance**: Supplier scorecards, cycle times
5. **Data Summary**: System-wide statistics and health

---

## 🚀 **Technology Stack**

### **Backend**
- **Framework**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL with AsyncSQLAlchemy
- **Authentication**: JWT tokens with role-based access
- **Optimization**: Google OR-Tools (CP-SAT, GLOP, SCIP, CBC)
- **File Processing**: openpyxl for Excel operations
- **API Documentation**: Swagger/OpenAPI

### **Frontend**
- **Framework**: React 18 with TypeScript
- **UI Library**: Material-UI (MUI) v5
- **State Management**: React Hooks (useState, useEffect)
- **Charts**: Recharts for data visualization
- **HTTP Client**: Axios with interceptors
- **Routing**: React Router v6

### **Infrastructure**
- **Containerization**: Docker & Docker Compose
- **Database**: PostgreSQL 14+
- **Reverse Proxy**: Nginx (in production)
- **File Storage**: Local filesystem (configurable)

---

## 🔄 **Data Flow Architecture**

### **1. Data Ingestion**
```
Excel Import → Data Validation → Database Storage → Indexing
```

### **2. Optimization Process**
```
Requirements → Constraint Building → Solver Execution → Result Processing → Decision Generation
```

### **3. Decision Lifecycle**
```
Optimization → Proposal → Review → Finalization → Execution → Tracking
```

### **4. Financial Tracking**
```
Budget Planning → Cost Optimization → Payment Scheduling → Cash Flow → Reporting
```

---

## 📈 **Performance & Scalability**

### **Database Optimization**
- **Indexing**: Strategic indexes on frequently queried fields
- **Async Operations**: Non-blocking database operations
- **Connection Pooling**: Efficient database connection management
- **Query Optimization**: Optimized SQL queries with proper JOINs

### **Caching Strategy**
- **Session Caching**: User session data
- **Query Result Caching**: Frequently accessed data
- **Static Asset Caching**: Frontend assets

### **Scalability Features**
- **Horizontal Scaling**: Stateless backend design
- **Database Sharding**: Project-based data partitioning
- **Async Processing**: Non-blocking optimization execution
- **Resource Management**: Memory and CPU optimization

---

## 🔧 **Configuration & Deployment**

### **Environment Variables**
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/procurement_dss

# Security
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Optimization
MAX_OPTIMIZATION_TIME=300
DEFAULT_SOLVER=CP_SAT
```

### **Docker Configuration**
```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: procurement_dss
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

---

## 🛡️ **Security Features**

### **Authentication**
- JWT-based token authentication
- Secure password hashing (bcrypt)
- Session management
- Token expiration handling

### **Authorization**
- Role-based access control (RBAC)
- Project-level permissions
- API endpoint protection
- Data filtering by user role

### **Data Security**
- SQL injection prevention
- XSS protection
- CORS configuration
- Input validation and sanitization

---

## 📋 **API Response Formats**

### **Success Response**
```json
{
  "data": {...},
  "message": "Operation successful",
  "status": "success"
}
```

### **Error Response**
```json
{
  "detail": "Error message",
  "status_code": 400,
  "type": "validation_error"
}
```

### **Pagination**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

---

## 🔍 **Monitoring & Logging**

### **Application Logging**
- **Structured Logging**: JSON-formatted logs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Request Tracking**: Request/response logging
- **Error Tracking**: Detailed error logging

### **Performance Monitoring**
- **Response Times**: API endpoint performance
- **Database Queries**: Query execution times
- **Optimization Metrics**: Solver performance
- **Resource Usage**: Memory and CPU monitoring

---

## 🚀 **Deployment Architecture**

### **Development Environment**
```
Frontend (React) ←→ Backend (FastAPI) ←→ Database (PostgreSQL)
     Port 3000         Port 8000           Port 5432
```

### **Production Environment**
```
Load Balancer → Frontend (Nginx) → Backend (FastAPI) → Database (PostgreSQL)
```

### **Deployment Process**
1. **Code Build**: Docker image creation
2. **Database Migration**: Schema updates
3. **Service Deployment**: Container orchestration
4. **Health Checks**: Service validation
5. **Traffic Routing**: Load balancer configuration

---

This technical architecture provides a comprehensive foundation for enterprise-level procurement decision support, with robust optimization capabilities, role-based security, and scalable infrastructure.
