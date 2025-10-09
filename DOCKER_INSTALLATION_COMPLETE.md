# 🐳 Docker Installation - Everything You Need to Know

## 🎯 Your System Runs in Docker - Special Instructions

Since your platform runs in Docker containers, here's your complete Docker-specific guide.

---

## ⚡ **FASTEST PATH - Run These 3 Commands:**

```powershell
# 1. Navigate to project
cd "C:\Old Laptop\D\Work\140407\cahs_flow_project"

# 2. Install in Docker (rebuilds backend container)
.\install_ortools_enhancements_docker.bat

# 3. Test in Docker
docker-compose exec backend python test_enhanced_optimization.py
```

**Total Time: 5 minutes**  
**Then open:** `http://localhost:3000/optimization-enhanced`

---

## 📋 What the Docker Installer Does

```powershell
.\install_ortools_enhancements_docker.bat
```

**Steps it performs:**
1. ✅ Stops existing containers (`docker-compose down`)
2. ✅ Rebuilds backend with new dependencies (`docker-compose build backend`)
3. ✅ Starts all services (`docker-compose up -d`)
4. ✅ Verifies NetworkX installed in container
5. ✅ Verifies OR-Tools available
6. ✅ Verifies enhanced optimizer working
7. ✅ Shows service status

**Why rebuild backend?**
- `requirements.txt` now includes `networkx==3.2.1`
- Docker build reads requirements.txt
- Installs all dependencies automatically
- No manual pip install needed inside container!

---

## 🔍 Understanding Your Docker Setup

### Your docker-compose.yml Structure:

```yaml
services:
  postgres:  # Database
    - Port 5432
    - Data persisted in volume
    
  backend:   # FastAPI + OR-Tools
    - Port 8000
    - Built from ./backend/Dockerfile
    - Reads requirements.txt ← networkx added here!
    - Auto-reload enabled
    - Volume mounted: ./backend → /app
    
  frontend:  # React UI
    - Port 3000
    - Built from ./frontend/Dockerfile
    - Auto-reload enabled
    - Volume mounted: ./frontend → /app
```

### Key Insight:

**Your code is volume-mounted**, which means:
- ✅ Code changes reflected immediately (no rebuild needed)
- ✅ Backend auto-reloads on Python file changes
- ✅ Frontend auto-reloads on React file changes
- ⚠️ Dependency changes need rebuild

**When you need to rebuild:**
- ✅ After updating `requirements.txt` ← We did this!
- ✅ After updating `package.json`
- ✅ After Dockerfile changes
- ❌ NOT needed for regular code changes

---

## ✅ Verification in Docker

### Check All Services Running

```powershell
docker-compose ps
```

**Should show:**
```
NAME                  STATUS    PORTS
backend               Up        0.0.0.0:8000->8000/tcp
frontend              Up        0.0.0.0:3000->3000/tcp
postgres              Up        0.0.0.0:5432->5432/tcp
```

### Check NetworkX Installed

```powershell
docker-compose exec backend python -c "import networkx; print('✅ NetworkX:', networkx.__version__)"
```

**Should show:**
```
✅ NetworkX: 3.2.1
```

### Check Enhanced Optimizer

```powershell
docker-compose exec backend python -c "from app.optimization_engine_enhanced import EnhancedProcurementOptimizer, SolverType; print('✅ Enhanced optimizer ready')"
```

**Should show:**
```
✅ Enhanced optimizer ready
```

### Quick Solver Test

```powershell
docker-compose exec backend python -c "
from ortools.sat.python import cp_model
from ortools.linear_solver import pywraplp

print('✅ CP-SAT available')
glop = pywraplp.Solver.CreateSolver('GLOP')
print('✅ GLOP:', 'Available' if glop else 'Not Available')
cbc = pywraplp.Solver.CreateSolver('CBC')
print('✅ CBC:', 'Available' if cbc else 'Not Available')
"
```

---

## 🧪 Testing in Docker

### Automated Test

```powershell
# Run the complete test suite inside Docker
docker-compose exec backend python test_enhanced_optimization.py
```

### Check Optimization Results Saved

```powershell
# Access database container
docker-compose exec postgres psql -U postgres -d procurement_dss

# In PostgreSQL shell:
SELECT COUNT(*) FROM optimization_runs;
SELECT COUNT(*) FROM optimization_results;
\q
```

### View Backend Logs During Optimization

```powershell
# Open in separate terminal
docker-compose logs -f backend

# Then run optimization from browser
# Watch logs show:
# - "Loaded X projects, Y items"
# - "Generated 5 proposal(s)"
# - "Saved optimization run to database"
```

---

## 🔧 Docker Commands You'll Use Daily

### Starting Your Day

```powershell
# Start all services
docker-compose up -d

# Check they're running
docker-compose ps

# View logs (optional)
docker-compose logs -f backend
```

### During Development

```powershell
# View logs while working
docker-compose logs -f backend

# Run tests
docker-compose exec backend python test_enhanced_optimization.py

# Access database
docker-compose exec postgres psql -U postgres -d procurement_dss

# Restart if needed
docker-compose restart backend
```

### End of Day

```powershell
# Stop services (preserves data)
docker-compose down

# Or leave running (recommended)
# Docker runs in background
```

---

## 🐛 Docker-Specific Troubleshooting

### Issue: "NetworkX not found" after rebuild

```powershell
Solution:
# Force clean rebuild
docker-compose build --no-cache backend
docker-compose up -d
```

### Issue: Changes not reflecting

```powershell
Solution:
# For Python changes (should auto-reload):
docker-compose restart backend

# For requirements.txt changes:
docker-compose build backend
docker-compose up -d backend
```

### Issue: Container keeps restarting

```powershell
Solution:
# Check logs for error
docker-compose logs backend

# Common causes:
# 1. Database not ready
docker-compose up -d postgres
timeout /t 5
docker-compose up -d backend

# 2. Syntax error in code
# Check logs, fix error, save file (auto-reloads)
```

### Issue: Port already in use

```powershell
Solution:
# Check what's using port 8000
netstat -ano | findstr :8000

# Stop conflicting process or:
docker-compose down
# Change port in docker-compose.yml
# ports: - "8001:8000"  # Use 8001 instead
docker-compose up -d
```

### Issue: Out of disk space

```powershell
Solution:
# Clean up Docker
docker system prune -a

# Remove old images
docker image prune -a

# Check space
docker system df
```

---

## 📊 Database Access in Docker

### Quick Database Queries

```powershell
# One-liner SQL query
docker-compose exec postgres psql -U postgres -d procurement_dss -c "SELECT COUNT(*) FROM optimization_runs;"

# Check finalized decisions
docker-compose exec postgres psql -U postgres -d procurement_dss -c "SELECT status, COUNT(*) FROM finalized_decisions GROUP BY status;"

# View latest optimization run
docker-compose exec postgres psql -U postgres -d procurement_dss -c "SELECT * FROM optimization_runs ORDER BY run_timestamp DESC LIMIT 1;"
```

### Interactive Database Session

```powershell
# Access PostgreSQL shell
docker-compose exec postgres psql -U postgres -d procurement_dss

# Then run SQL commands:
\dt                    # List tables
SELECT * FROM optimization_runs ORDER BY run_timestamp DESC LIMIT 5;
SELECT COUNT(*) FROM finalized_decisions WHERE status = 'LOCKED';
\q                     # Exit
```

---

## 🎯 Complete Docker Workflow

### First Time Setup (Today)

```powershell
# 1. Install
.\install_ortools_enhancements_docker.bat

# 2. Test
docker-compose exec backend python test_enhanced_optimization.py

# 3. Open browser
start http://localhost:3000/optimization-enhanced

# 4. Monitor logs (optional, new terminal)
docker-compose logs -f backend

# 5. Run your first optimization!
```

### Daily Usage (Ongoing)

```powershell
# Morning: Start services
docker-compose up -d

# Check status
docker-compose ps

# Open browser
start http://localhost:3000/optimization-enhanced

# Use the system normally!

# Evening: Stop services (optional)
docker-compose down
```

### When Code Changes

```powershell
# Python/React code changes:
# → Auto-reload (no action needed!)

# requirements.txt changes:
docker-compose build backend
docker-compose up -d backend

# package.json changes:
docker-compose build frontend
docker-compose up -d frontend
```

---

## 🎨 Docker-Enhanced Features

### Advantages of Docker Setup

✅ **Consistency:** Same environment everywhere  
✅ **Isolation:** No conflicts with other projects  
✅ **Easy Setup:** One command to start everything  
✅ **Portability:** Works on any machine with Docker  
✅ **Auto-Reload:** Changes reflected immediately  
✅ **Clean State:** Easy to reset and start fresh  

### Your Enhanced System in Docker

```
┌──────────────────────────────────────────┐
│  Docker Container: backend               │
│  ├─ Python 3.11                         │
│  ├─ FastAPI                             │
│  ├─ OR-Tools 9.8                        │
│  ├─ NetworkX 3.2.1 ← NEW!               │
│  ├─ Enhanced Optimizer ← NEW!           │
│  └─ Auto-reload enabled                 │
└──────────────────────────────────────────┘
           ↕️ Network
┌──────────────────────────────────────────┐
│  Docker Container: postgres              │
│  ├─ PostgreSQL 15                       │
│  ├─ Database: procurement_dss           │
│  ├─ Volume mounted (data persists)      │
│  └─ Tables: optimization_runs, etc.     │
└──────────────────────────────────────────┘
           ↕️ Network
┌──────────────────────────────────────────┐
│  Docker Container: frontend              │
│  ├─ Node.js                             │
│  ├─ React                               │
│  ├─ Enhanced Optimization Page ← NEW!   │
│  └─ Auto-reload enabled                 │
└──────────────────────────────────────────┘
```

---

## 📝 Docker-Specific Notes

### What's Different from Local Setup:

| Aspect | Local Setup | Docker Setup |
|--------|-------------|--------------|
| **Installation** | `pip install` | `docker-compose build` |
| **Testing** | `python test.py` | `docker-compose exec backend python test.py` |
| **Logs** | Terminal output | `docker-compose logs -f backend` |
| **Database** | Local PostgreSQL | Docker PostgreSQL container |
| **Port Access** | Direct | Mapped (3000→3000, 8000→8000) |
| **File Changes** | Direct | Volume-mounted (instant sync) |

### What's the SAME:

| Aspect | Same! |
|--------|-------|
| **Frontend URL** | http://localhost:3000 ✅ |
| **Backend API** | http://localhost:8000 ✅ |
| **Features** | All identical ✅ |
| **Documentation** | All applies ✅ |
| **Workflow** | Exact same ✅ |

---

## ✅ Docker Installation Checklist

After running `.\install_ortools_enhancements_docker.bat`:

- [ ] Backend container rebuilt successfully
- [ ] All services started (docker-compose ps shows 3 running)
- [ ] NetworkX verified in container
- [ ] OR-Tools verified in container
- [ ] Enhanced optimizer verified
- [ ] Tests pass (docker-compose exec backend python test...)
- [ ] Frontend accessible (http://localhost:3000)
- [ ] Backend accessible (http://localhost:8000/docs)
- [ ] Can run optimization from UI
- [ ] Optimization results saved to database

---

## 🚀 You're Ready!

**Your Docker-based system now has:**

✅ **All enhancements installed in Docker**  
✅ **NetworkX integrated**  
✅ **4 solvers available**  
✅ **Enhanced optimizer operational**  
✅ **Complete finalization flow**  
✅ **Automatic data persistence**  
✅ **All services running in containers**  

**Next:** Open `http://localhost:3000/optimization-enhanced` and start optimizing!

---

## 📞 Quick Help

**Installation Issues:**
- See `DOCKER_SETUP_GUIDE.md`

**Usage Guide:**
- See `RUN_THIS_NOW.md` (now updated for Docker!)
- See `OPTIMIZATION_FINALIZATION_FLOW.md`

**Docker Commands:**
- See `DOCKER_SETUP_GUIDE.md` for complete reference

---

**🎊 Your Docker-based procurement optimization system is ready! 🎊**

