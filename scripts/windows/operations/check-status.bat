@echo off
REM Check Procurement DSS System Status

echo ========================================
echo  Procurement DSS - System Status
echo ========================================
echo.

REM Check Docker running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo X Docker is NOT running
    echo   Please start Docker Desktop
    pause
    exit /b 1
)

echo + Docker is running
echo.

REM Check container status
echo Container Status:
echo.
docker-compose ps

echo.
echo ========================================

REM Check if services are healthy
docker-compose ps | findstr "Up" >nul 2>&1
if %errorlevel% equ 0 (
    echo + Services are RUNNING
    
    echo.
    echo Access Points:
    echo   Frontend:    http://localhost:3000
    echo   Backend:     http://localhost:8000
    echo   API Docs:    http://localhost:8000/docs
    
    echo.
    echo Database Status:
    docker-compose exec postgres psql -U postgres -d procurement_dss -c "SELECT 'Database Connected' as status;" 2>nul
    
    if %errorlevel% equ 0 (
        echo.
        echo Data Verification:
        docker-compose exec postgres psql -U postgres -d procurement_dss -c "SELECT 'Optimization Runs: ' || COUNT(*)::text FROM optimization_runs;" 2>nul
        docker-compose exec postgres psql -U postgres -d procurement_dss -c "SELECT 'Finalized Decisions: ' || COUNT(*)::text FROM finalized_decisions;" 2>nul
        docker-compose exec postgres psql -U postgres -d procurement_dss -c "SELECT 'Projects: ' || COUNT(*)::text FROM projects;" 2>nul
        docker-compose exec postgres psql -U postgres -d procurement_dss -c "SELECT 'Budget Periods: ' || COUNT(*)::text FROM budget_data;" 2>nul
    )
    
    echo.
    echo Volume Status:
    docker volume inspect cahs_flow_project_postgres_data >nul 2>&1
    if %errorlevel% equ 0 (
        echo + Database volume EXISTS (data is safe)
    ) else (
        echo X Database volume NOT FOUND (data may be lost)
    )
    
) else (
    echo X Services are NOT running
    echo.
    echo To start services:
    echo   start.bat
)

echo.
echo ========================================
echo.

pause

