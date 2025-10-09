# Docker Setup Guide - OR-Tools Enhancement

## 🐳 Docker-Specific Installation & Testing

Since your platform runs in Docker, here are the Docker-specific procedures.

---

## ⚡ Quick Start (5 minutes)

```powershell
# 1. Install enhancements in Docker
.\install_ortools_enhancements_docker.bat

# 2. Test in Docker
docker-compose exec backend python test_enhanced_optimization.py

# 3. Open browser
# Navigate to: http://localhost:3000/optimization-enhanced
```

---

## 📋 Detailed Docker Setup

### Step 1: Update Backend Container (2 minutes)

The `networkx` dependency is already added to `backend/requirements.txt`, so we just need to rebuild:

```powershell
# Stop containers
docker-compose down

# Rebuild backend (installs networkx automatically)
docker-compose build backend

# Start all services
docker-compose up -d

# Wait for services to start
timeout /t 10
```

**What happens:**
- Docker reads `requirements.txt`
- Sees `networkx==3.2.1`
- Installs it during build
- Backend container now has enhanced optimizer

---

### Step 2: Verify Installation (1 minute)

```powershell
# Check if services are running
docker-compose ps

# Expected output:
# backend    running    0.0.0.0:8000->8000/tcp
# frontend   running    0.0.0.0:3000->3000/tcp
# db         running    0.0.0.0:5432->5432/tcp

# Verify NetworkX in container
docker-compose exec backend python -c "import networkx; print('NetworkX:', networkx.__version__)"

# Verify enhanced optimizer
docker-compose exec backend python -c "from app.optimization_engine_enhanced import EnhancedProcurementOptimizer; print('Enhanced optimizer OK')"
```

---

### Step 3: Run Tests in Docker (2 minutes)

```powershell
# Run automated test script inside backend container
docker-compose exec backend python test_enhanced_optimization.py
```

**Expected Output:**
```
🧪 Testing Enhanced Optimization Installation
==============================================================
1️⃣ Testing imports...
   ✅ All imports successful
2️⃣ Testing solver availability...
   ✅ CP-SAT available
   ✅ GLOP available
   ✅ CBC available
3️⃣ Testing database connectivity...
   ✅ Database connected
4️⃣ Testing optimizer instantiation...
   ✅ Optimizer created successfully
5️⃣ Running quick optimization test...
   ✅ Optimization completed

🎉 Installation successful! Core solvers ready.
```

---

## 🛠️ Docker Commands Reference

### Container Management

```powershell
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart backend only
docker-compose restart backend

# Rebuild backend (after code changes)
docker-compose build backend
docker-compose up -d backend

# View running containers
docker-compose ps

# View logs
docker-compose logs -f backend      # Backend logs
docker-compose logs -f frontend     # Frontend logs
docker-compose logs -f              # All logs
```

### Accessing Containers

```powershell
# Execute command in backend container
docker-compose exec backend [command]

# Access backend shell
docker-compose exec backend bash

# Access Python shell in backend
docker-compose exec backend python

# Run Python script in backend
docker-compose exec backend python test_enhanced_optimization.py

# Access database
docker-compose exec db psql -U postgres -d procurement_db
```

### Testing Commands

```powershell
# Run enhanced optimizer test
docker-compose exec backend python test_enhanced_optimization.py

# Test imports
docker-compose exec backend python -c "import networkx, ortools; print('OK')"

# Test specific solver
docker-compose exec backend python -c "from ortools.linear_solver import pywraplp; s=pywraplp.Solver.CreateSolver('GLOP'); print('GLOP:', 'OK' if s else 'FAIL')"

# Check installed packages
docker-compose exec backend pip list | grep -E "networkx|ortools"
```

### Database Queries in Docker

```powershell
# Access PostgreSQL in container
docker-compose exec db psql -U postgres -d procurement_db

# Then run SQL:
# SELECT COUNT(*) FROM optimization_runs;
# SELECT * FROM optimization_runs ORDER BY run_timestamp DESC LIMIT 5;
# \q to exit
```

---

## 🔄 Update Workflow for Docker

### When Code Changes

```powershell
# 1. Code is changed in your editor (VSCode, etc.)
# 2. Changes are automatically reflected in containers (volume mount)
# 3. Backend auto-reloads (uvicorn --reload)
# 4. Frontend auto-reloads (npm start in watch mode)

# No rebuild needed for Python/React code changes!
```

### When Dependencies Change

```powershell
# If requirements.txt changes:
docker-compose build backend
docker-compose up -d backend

# If package.json changes:
docker-compose build frontend
docker-compose up -d frontend
```

---

## 🧪 Testing in Docker

### Quick Test (30 seconds)

```powershell
# Test that everything works
docker-compose exec backend python -c "
from app.optimization_engine_enhanced import EnhancedProcurementOptimizer, SolverType
print('✅ Enhanced optimizer imported successfully')
print('✅ Solvers:', ', '.join([s.value for s in SolverType]))
"
```

### Full Test (2 minutes)

```powershell
# Run comprehensive test suite
docker-compose exec backend python test_enhanced_optimization.py
```

### Manual API Test

```powershell
# Test solver-info endpoint
curl http://localhost:8000/finance/solver-info

# Test enhanced optimization (with auth token)
# First get token:
$token = (Invoke-RestMethod -Uri "http://localhost:8000/auth/login" -Method Post -Body (@{username="admin";password="yourpassword"} | ConvertTo-Json) -ContentType "application/json").access_token

# Then run optimization:
Invoke-RestMethod -Uri "http://localhost:8000/finance/optimize-enhanced?solver_type=CP_SAT&generate_multiple_proposals=true" -Method Post -Headers @{Authorization="Bearer $token"} -Body (@{max_time_slots=12;time_limit_seconds=60} | ConvertTo-Json) -ContentType "application/json"
```

---

## 📊 Docker-Specific Troubleshooting

### Issue: "NetworkX not found" in Docker

```powershell
Solution:
# Force rebuild backend
docker-compose build --no-cache backend
docker-compose up -d
```

### Issue: Changes not reflecting

```powershell
Solution:
# Backend changes:
docker-compose restart backend

# If still not working:
docker-compose down
docker-compose up -d
```

### Issue: Database connection failed

```powershell
Solution:
# Check if db container is running
docker-compose ps

# If not, start it:
docker-compose up -d db

# Wait a few seconds, then restart backend:
docker-compose restart backend
```

### Issue: Port already in use

```powershell
Solution:
# Check what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Stop existing containers
docker-compose down

# Start fresh
docker-compose up -d
```

### Issue: Out of memory

```powershell
Solution:
# Increase Docker memory in Docker Desktop settings
# Settings → Resources → Memory → Increase to 4GB+

# Or run without frontend initially:
docker-compose up -d backend db
```

---

## 🔍 Monitoring in Docker

### View Real-Time Logs

```powershell
# Backend logs (optimization runs show here)
docker-compose logs -f backend

# Frontend logs
docker-compose logs -f frontend

# All logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Check Container Health

```powershell
# Container status
docker-compose ps

# Resource usage
docker stats

# Container details
docker-compose exec backend ps aux
```

---

## 🚀 Production Docker Deployment

### Build for Production

```powershell
# Build with production settings
docker-compose -f docker-compose.yml build

# Start in production mode
docker-compose -f docker-compose.yml up -d

# Check status
docker-compose -f docker-compose.yml ps
```

### Environment Variables

Make sure your `.env` file or docker-compose.yml has:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/procurement_db

# API
API_URL=http://backend:8000

# Add if needed:
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO
```

---

## 📦 Docker Volume Management

### Data Persistence

```powershell
# List volumes
docker volume ls

# Backup database
docker-compose exec db pg_dump -U postgres procurement_db > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres procurement_db < backup.sql
```

---

## ⚡ Quick Commands for Daily Use

### Start Your Day

```powershell
# Start everything
docker-compose up -d

# Check status
docker-compose ps

# Open in browser
start http://localhost:3000/optimization-enhanced
```

### During Development

```powershell
# View backend logs (see optimization progress)
docker-compose logs -f backend

# Run tests
docker-compose exec backend python test_enhanced_optimization.py

# Access database
docker-compose exec db psql -U postgres -d procurement_db
```

### End of Day

```powershell
# Stop all services (preserves data)
docker-compose down

# Stop and remove volumes (CAUTION: deletes data)
docker-compose down -v
```

---

## 🎯 Docker-Specific First Run

### Complete Flow in Docker

```powershell
# 1. Rebuild and start
.\install_ortools_enhancements_docker.bat

# 2. Verify installation
docker-compose exec backend python test_enhanced_optimization.py

# 3. Open browser
start http://localhost:3000

# 4. Login and navigate to /optimization-enhanced

# 5. Run optimization

# 6. Monitor backend logs in another terminal
docker-compose logs -f backend

# Look for:
# - "Loaded X projects, Y items"
# - "Generated 5 proposal(s)"
# - "Saved optimization run to database"
```

---

## 🐛 Docker-Specific Troubleshooting

### Container won't start

```powershell
# Check logs
docker-compose logs backend

# Common issues:
# 1. Database not ready
docker-compose up -d db
timeout /t 5
docker-compose up -d backend

# 2. Port conflict
docker-compose down
netstat -ano | findstr :8000
# Kill process using port, then:
docker-compose up -d
```

### Cannot access localhost:3000

```powershell
# Check if container is running
docker-compose ps frontend

# Check logs
docker-compose logs frontend

# Rebuild if needed
docker-compose build frontend
docker-compose up -d frontend
```

### Database errors

```powershell
# Reset database (CAUTION: deletes data)
docker-compose down
docker volume rm cahs_flow_project_postgres_data
docker-compose up -d

# Or just restart
docker-compose restart db
timeout /t 5
docker-compose restart backend
```

---

## 📊 Verify Installation in Docker

### Automated Verification

```powershell
# Run this one command to verify everything:
docker-compose exec backend python -c "
import networkx as nx
from ortools.sat.python import cp_model
from ortools.linear_solver import pywraplp
from app.optimization_engine_enhanced import EnhancedProcurementOptimizer, SolverType

print('✅ NetworkX:', nx.__version__)
print('✅ CP-SAT: Available')

glop = pywraplp.Solver.CreateSolver('GLOP')
print('✅ GLOP:', 'Available' if glop else 'Not Available')

cbc = pywraplp.Solver.CreateSolver('CBC')
print('✅ CBC:', 'Available' if cbc else 'Not Available')

print('✅ Enhanced Optimizer: Ready')
print('')
print('🎉 All systems operational!')
"
```

---

## 🎯 Success Criteria

Your Docker installation is successful when:

- [x] `docker-compose ps` shows all services running
- [x] `docker-compose exec backend python test_enhanced_optimization.py` passes
- [x] Can access http://localhost:3000
- [x] Can access http://localhost:8000/docs
- [x] Advanced Optimization page loads
- [x] Can run optimization successfully

---

## 💡 Pro Tips for Docker

**1. Use Docker Desktop Dashboard**
- Visual container management
- Easy log viewing
- Resource monitoring

**2. Keep Containers Running**
```powershell
# Don't down/up repeatedly
# Just restart services as needed:
docker-compose restart backend
```

**3. View Logs in Real-Time**
```powershell
# Split terminal or use Windows Terminal tabs:
# Tab 1: docker-compose logs -f backend
# Tab 2: docker-compose logs -f frontend
# Tab 3: Your commands
```

**4. Database Access**
```powershell
# Save this as a shortcut:
docker-compose exec db psql -U postgres -d procurement_db
```

**5. Quick Rebuild**
```powershell
# After pulling updates:
docker-compose build && docker-compose up -d
```

---

## 🚀 Your Next Commands

```powershell
# Right now:
.\install_ortools_enhancements_docker.bat

# After installation:
docker-compose exec backend python test_enhanced_optimization.py

# View logs while testing:
docker-compose logs -f backend

# Open browser:
start http://localhost:3000/optimization-enhanced

# Check database:
docker-compose exec db psql -U postgres -d procurement_db -c "SELECT COUNT(*) FROM optimization_runs;"
```

---

## 📚 Docker-Specific Documentation

**Quick Reference:**
- `install_ortools_enhancements_docker.bat` - Docker installer
- `DOCKER_SETUP_GUIDE.md` - This file
- `docker-compose.yml` - Your container configuration

**General Documentation:**
- All other guides apply the same!
- Just use Docker commands instead of local commands

---

## ✅ Verification Checklist

After running installation script:

- [ ] All containers running (`docker-compose ps`)
- [ ] NetworkX installed in backend (`docker-compose exec backend python -c "import networkx"`)
- [ ] Tests pass (`docker-compose exec backend python test_enhanced_optimization.py`)
- [ ] Frontend accessible (http://localhost:3000)
- [ ] Backend accessible (http://localhost:8000/docs)
- [ ] Can run optimization from UI
- [ ] Can save and finalize proposals

---

## 🎉 You're Ready!

**Your Docker-based system now has:**
- ✅ Enhanced optimization engine
- ✅ All 4 solvers (CP_SAT, GLOP, SCIP, CBC)
- ✅ Multi-proposal generation
- ✅ Complete finalization flow
- ✅ Automatic data persistence

**All running in Docker containers! 🐳**

---

*For detailed usage, see the other documentation files - all procedures work the same in Docker!*

