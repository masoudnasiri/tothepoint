# Project Structure Overview

This document provides a comprehensive overview of the Procurement DSS project structure.

```
cahs_flow_project/
├── README.md                          # Main project documentation
├── SETUP.md                           # Detailed setup guide
├── PROJECT_STRUCTURE.md               # This file
├── docker-compose.yml                 # Docker orchestration
├── start.sh                          # Startup script
├── stop.sh                           # Stop script
│
├── backend/                          # FastAPI Backend
│   ├── Dockerfile                    # Backend Docker image
│   ├── requirements.txt              # Python dependencies
│   ├── init.sql                      # Database initialization
│   └── app/                          # Application code
│       ├── __init__.py
│       ├── main.py                   # FastAPI application entry point
│       ├── config.py                 # Configuration settings
│       ├── database.py               # Database connection and setup
│       ├── models.py                 # SQLAlchemy database models
│       ├── schemas.py                # Pydantic schemas for API validation
│       ├── auth.py                   # Authentication and authorization
│       ├── crud.py                   # Database CRUD operations
│       ├── optimization_engine.py    # Google OR-Tools CP-SAT optimization
│       ├── excel_handler.py          # Excel import/export functionality
│       └── routers/                  # API route modules
│           ├── __init__.py
│           ├── auth.py               # Authentication endpoints
│           ├── users.py              # User management endpoints
│           ├── projects.py           # Project management endpoints
│           ├── items.py              # Project items endpoints
│           ├── procurement.py        # Procurement options endpoints
│           ├── finance.py            # Finance and optimization endpoints
│           └── excel.py              # Excel import/export endpoints
│
└── frontend/                         # React Frontend
    ├── Dockerfile                    # Frontend Docker image
    ├── package.json                  # Node.js dependencies
    ├── public/                       # Static assets
    │   └── index.html
    └── src/                          # React application source
        ├── index.tsx                 # Application entry point
        ├── App.tsx                   # Main application component
        ├── types/                    # TypeScript type definitions
        │   └── index.ts
        ├── services/                 # API service layer
        │   └── api.ts
        ├── contexts/                 # React contexts
        │   └── AuthContext.tsx
        ├── components/               # Reusable components
        │   ├── Layout.tsx            # Main layout with navigation
        │   └── ProtectedRoute.tsx    # Route protection
        └── pages/                    # Page components
            ├── LoginPage.tsx         # Login page
            ├── DashboardPage.tsx     # Dashboard with statistics
            ├── ProjectsPage.tsx      # Project management
            ├── ProjectItemsPage.tsx  # Project items management
            ├── ProcurementPage.tsx   # Procurement options
            ├── FinancePage.tsx       # Budget management
            ├── OptimizationPage.tsx  # Optimization results
            └── UsersPage.tsx         # User management (admin)
```

## Backend Architecture

### Core Components

1. **main.py** - FastAPI application with middleware, CORS, and route registration
2. **config.py** - Environment-based configuration management
3. **database.py** - Async SQLAlchemy setup with connection management
4. **models.py** - Database models with relationships and constraints
5. **schemas.py** - Pydantic models for request/response validation
6. **auth.py** - JWT authentication and RBAC permission system

### Business Logic

1. **crud.py** - Database operations with async/await patterns
2. **optimization_engine.py** - Google OR-Tools CP-SAT solver implementation
3. **excel_handler.py** - Pandas-based Excel import/export with validation

### API Structure

- **auth.py** - Login, registration, token refresh
- **users.py** - User CRUD operations (admin only)
- **projects.py** - Project management and assignments
- **items.py** - Project item management (PM access)
- **procurement.py** - Procurement options (procurement specialist access)
- **finance.py** - Budget management and optimization (finance access)
- **excel.py** - Excel template download and data import/export

## Frontend Architecture

### Component Structure

1. **Layout.tsx** - Main application layout with navigation and user menu
2. **ProtectedRoute.tsx** - Route protection based on authentication
3. **AuthContext.tsx** - Global authentication state management

### Page Components

Each page corresponds to a major functional area:
- **LoginPage** - Authentication interface
- **DashboardPage** - System overview and statistics
- **ProjectsPage** - Project listing and management
- **ProjectItemsPage** - Item requirements management
- **ProcurementPage** - Supplier options and terms
- **FinancePage** - Budget configuration
- **OptimizationPage** - Results visualization
- **UsersPage** - User administration

### Services and Types

- **api.ts** - Centralized API client with axios configuration
- **types/index.ts** - TypeScript interfaces for all data models

## Database Schema

### Core Tables

1. **users** - User accounts with roles and authentication
2. **projects** - Project definitions and metadata
3. **project_assignments** - Many-to-many user-project relationships
4. **project_items** - Item requirements per project
5. **procurement_options** - Supplier options with payment terms
6. **budget_data** - Available budget per time period
7. **optimization_results** - Optimization run results

### Key Relationships

- Users can be assigned to multiple projects
- Projects contain multiple items
- Items can have multiple procurement options
- Optimization results link items to selected options

## Security Model

### Authentication
- JWT tokens with configurable expiration
- Secure password hashing with bcrypt
- Automatic token refresh

### Authorization
- Role-based access control (RBAC)
- Data isolation by user role
- API endpoint protection
- Frontend route protection

### Data Privacy
- Project Managers see only assigned projects
- Procurement specialists see only item codes, not project details
- Finance users see all data but cannot modify project/items
- Admin has full system access

## Optimization Engine

### CP-SAT Model
- Decision variables: buy[p,i,o,t] (project, item, option, time)
- Constraints: demand fulfillment, time windows, lead times, budget
- Objective: minimize total procurement cost

### Key Features
- Multi-project optimization
- Flexible payment terms (cash/installments)
- Bundling discounts
- Lead time constraints (LOMC)
- Budget constraint enforcement

## Excel Integration

### Import Features
- Template-based data entry
- Validation and error reporting
- Bulk data processing
- Role-based import restrictions

### Export Features
- Current data export
- Template downloads
- Role-based export restrictions
- Multiple format support (.xlsx, .xls)

## Deployment

### Docker Configuration
- Multi-service docker-compose setup
- Health checks for service dependencies
- Volume persistence for database
- Environment-based configuration

### Development vs Production
- Development: Hot reload, debug mode, sample data
- Production: Optimized builds, secure configuration, monitoring

## Performance Considerations

### Backend
- Async/await for database operations
- Connection pooling
- Query optimization with indexes
- CP-SAT solver timeout configuration

### Frontend
- Material-UI component optimization
- Lazy loading for large datasets
- Efficient state management
- Responsive design

### Database
- Proper indexing on foreign keys
- Query optimization
- Connection management
- Data archiving for large datasets
