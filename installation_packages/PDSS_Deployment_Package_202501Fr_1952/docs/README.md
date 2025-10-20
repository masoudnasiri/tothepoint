# Project Procurement & Financial Optimization Decision Support System (DSS)

A comprehensive web-based system for optimizing procurement and financial planning across multiple concurrent projects using Google OR-Tools CP-SAT solver.

## 🏗️ Architecture

- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: React 18+ with TypeScript and Material-UI
- **Database**: PostgreSQL
- **Optimization Engine**: Google OR-Tools (CP-SAT Solver)
- **Authentication**: JWT-based RBAC system

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### One-Command Deployment

#### Windows
```cmd
# Run setup check first
setup-windows.bat

# Start the system
start.bat
```

#### Linux/macOS
```bash
# Make scripts executable
chmod +x start.sh stop.sh

# Start the system
./start.sh
```

#### Manual (All Platforms)
```bash
docker-compose up --build -d
```

The system will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Default Login Credentials
| Role | Username | Password | Access |
|------|----------|----------|--------|
| Admin | admin | admin123 | Full system access |
| Project Manager | pm1 | pm123 | Project and item management |
| Procurement Specialist | proc1 | proc123 | Procurement options management |
| Finance User | finance1 | finance123 | Budget and optimization |

### Stop the System

#### Windows
```cmd
stop.bat
```

#### Linux/macOS
```bash
./stop.sh
```

#### Manual (All Platforms)
```bash
docker-compose down
```

### Windows Users
For detailed Windows setup instructions, see [WINDOWS_SETUP.md](WINDOWS_SETUP.md)

## 🔧 Development Setup

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### Database Setup
```bash
# Using Docker PostgreSQL
docker-compose up -d postgres

# Or local PostgreSQL
createdb procurement_dss
```

## 👥 User Roles & Permissions

### Admin
- Full system control
- User management
- Project creation and assignment
- Granular permission control

### Project Manager (PM)
- View assigned projects only
- Manage project items (demand definition)
- No access to financial/procurement data
- Define item requirements and delivery constraints

### Procurement Specialist
- Manage global item master list
- Define procurement options and suppliers
- Set payment terms and bundling discounts
- Cannot see project-specific requirements

### Finance User
- Global view of all demands and options
- Manage budget constraints per time period
- Execute optimization runs
- View results and analytics

## 📊 System Features

### Core Modules
1. **Project Planning**: Demand definition and management
2. **Procurement Hub**: Supply options and supplier management
3. **Finance & Strategy**: Budget management and optimization execution
4. **Results Dashboard**: Optimization results visualization

### Key Capabilities
- Multi-project optimization with CP-SAT solver
- Flexible payment terms (cash, installments)
- Bundling discounts and cash discounts
- Lead time constraints (LOMC)
- Budget constraint enforcement
- Excel import/export for bulk data entry
- Role-based access control (RBAC)
- Real-time optimization results
- Comprehensive dashboard analytics

### User Workflows

#### Project Manager Workflow
1. View assigned projects
2. Add/edit project items with requirements
3. Define delivery constraints and time windows
4. Export/import item data via Excel

#### Procurement Specialist Workflow
1. Manage global item master list
2. Add procurement options for each item
3. Set supplier terms and payment options
4. Configure bundling discounts
5. Export/import procurement data

#### Finance User Workflow
1. Set budget constraints per time period
2. View consolidated demand and supply data
3. Execute optimization runs
4. Analyze results and cost savings
5. Export optimization results

#### Admin Workflow
1. Manage users and roles
2. Create and assign projects
3. Monitor system-wide activity
4. Access all modules with full permissions

## 🗄️ Database Schema

The system uses PostgreSQL with the following core tables:
- `users` - User management and roles
- `projects` - Project definitions
- `project_items` - Item requirements per project
- `procurement_options` - Supply options with payment terms
- `budget_data` - Available budget per time period
- `optimization_results` - Optimization run results

## 🔒 Security

- JWT-based authentication
- Role-based access control (RBAC)
- Data isolation between user roles
- Secure API endpoints with permission checks

## 📈 Optimization Engine

The CP-SAT solver optimizes for:
- **Objective**: Minimize total procurement cost
- **Constraints**: 
  - Demand fulfillment (exactly once per item)
  - Time window restrictions
  - Lead time requirements
  - Budget limitations
  - Payment schedule compliance

## 🛠️ API Documentation

Interactive API documentation is available at `/docs` when running the backend server.

## 🔧 Troubleshooting

### Common Issues

1. **Port Conflicts**
   - Ensure ports 3000, 8000, and 5432 are available
   - Change ports in `docker-compose.yml` if needed

2. **Database Connection Issues**
   - Wait for PostgreSQL to fully start (30-60 seconds)
   - Check logs: `docker-compose logs postgres`

3. **Frontend Not Loading**
   - Verify backend is running: `docker-compose logs backend`
   - Check API URL configuration

4. **Optimization Fails**
   - Ensure sufficient budget data is configured
   - Verify procurement options exist for required items
   - Check lead time constraints

### Viewing Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Resetting System
```bash
# Stop and remove all data
docker-compose down -v

# Start fresh
docker-compose up --build
```

## 📚 API Documentation

The system provides comprehensive API documentation:

- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Key API Endpoints

#### Authentication
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info

#### Projects
- `GET /projects/` - List projects
- `POST /projects/` - Create project (admin only)
- `GET /projects/{id}` - Get project details

#### Project Items
- `GET /items/project/{id}` - List project items
- `POST /items/` - Create item (PM only)
- `PUT /items/{id}` - Update item

#### Procurement
- `GET /procurement/item-codes` - List item codes
- `GET /procurement/options` - List procurement options
- `POST /procurement/options` - Create option (procurement only)

#### Finance
- `GET /finance/dashboard` - Dashboard statistics
- `POST /finance/optimize` - Run optimization (finance only)
- `GET /finance/optimization-results` - Get results

#### Excel Import/Export
- `GET /excel/templates/{type}` - Download templates
- `POST /excel/import/{type}` - Import data
- `GET /excel/export/{type}` - Export data

## 🏭 Production Deployment

For production deployment:

1. **Security**
   - Change default passwords and secret keys
   - Use environment variables for sensitive data
   - Set up SSL/TLS certificates
   - Configure proper CORS settings

2. **Database**
   - Use production-grade PostgreSQL instance
   - Set up automated backups
   - Configure connection pooling

3. **Performance**
   - Use reverse proxy (nginx/Apache)
   - Configure caching
   - Set up monitoring and logging

4. **Scalability**
   - Use container orchestration (Kubernetes)
   - Set up load balancing
   - Configure horizontal scaling

## 📈 Performance Considerations

- **Optimization Engine**: CP-SAT solver performance depends on problem size
- **Database**: Indexes are automatically created for optimal queries
- **Frontend**: Material-UI components are optimized for performance
- **Caching**: Consider Redis for session storage in production

## 🔒 Security Features

- JWT-based authentication with configurable expiration
- Role-based access control (RBAC)
- Data isolation between user roles
- Secure API endpoints with permission validation
- Password hashing with bcrypt
- CORS protection

## 📝 License

This project is proprietary software developed for internal use.
