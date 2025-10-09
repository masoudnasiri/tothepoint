@echo off
REM OR-Tools Enhancement Installation Script for Docker
REM This script installs the enhanced OR-Tools optimization features in Docker

echo ==================================
echo OR-Tools Enhancement Installation
echo For Docker Environment
echo ==================================
echo.

REM Step 1: Check if in correct directory
if not exist "docker-compose.yml" (
    echo X Error: Please run this script from the project root directory
    exit /b 1
)

echo + Project root directory detected
echo.

REM Step 2: Stop existing containers
echo Stopping existing containers...
docker-compose down

echo.

REM Step 3: Rebuild backend with new dependencies
echo Rebuilding backend container with new dependencies...
echo This will install networkx and update all packages...
docker-compose build backend

if %errorlevel% equ 0 (
    echo + Backend container rebuilt successfully
) else (
    echo X Failed to rebuild backend container
    exit /b 1
)

echo.

REM Step 4: Start all services
echo Starting all services...
docker-compose up -d

if %errorlevel% equ 0 (
    echo + All services started successfully
) else (
    echo X Failed to start services
    exit /b 1
)

echo.
echo Waiting for services to initialize (10 seconds)...
timeout /t 10 /nobreak >nul

echo.

REM Step 5: Verify installation in backend container
echo Verifying installation in Docker container...

docker-compose exec -T backend python -c "import networkx; print('+ NetworkX version:', networkx.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo ! Warning: Could not verify networkx installation
) else (
    echo + NetworkX verified in container
)

docker-compose exec -T backend python -c "import ortools; print('+ OR-Tools detected')" 2>nul
if %errorlevel% neq 0 (
    echo ! Warning: Could not verify OR-Tools installation
) else (
    echo + OR-Tools verified in container
)

docker-compose exec -T backend python -c "from app.optimization_engine_enhanced import EnhancedProcurementOptimizer; print('+ Enhanced optimizer verified')" 2>nul
if %errorlevel% neq 0 (
    echo ! Warning: Could not verify enhanced optimizer
) else (
    echo + Enhanced optimizer verified in container
)

echo.

REM Step 6: Summary
echo ==================================
echo + Installation Complete!
echo ==================================
echo.
echo Services Running:
docker-compose ps
echo.
echo Documentation Available:
echo   - OR_TOOLS_ENHANCEMENT_GUIDE.md (Comprehensive guide)
echo   - OR_TOOLS_QUICK_REFERENCE.md (Quick reference)
echo   - RUN_THIS_NOW.md (Setup commands)
echo   - OPTIMIZATION_FINALIZATION_FLOW.md (Complete flow)
echo.
echo Next Steps:
echo   1. Verify services are running:
echo      docker-compose ps
echo.
echo   2. Run tests in Docker:
echo      docker-compose exec backend python test_enhanced_optimization.py
echo.
echo   3. Navigate to the enhanced optimization page:
echo      http://localhost:3000/optimization-enhanced
echo.
echo   4. View backend logs:
echo      docker-compose logs -f backend
echo.
echo Quick Test:
echo   - Open browser to http://localhost:3000
echo   - Login as admin or finance user
echo   - Go to 'Advanced Optimization' in sidebar
echo   - Click 'Run Optimization' with CP_SAT solver
echo   - Review multiple proposals
echo.
echo Happy Optimizing!
pause

