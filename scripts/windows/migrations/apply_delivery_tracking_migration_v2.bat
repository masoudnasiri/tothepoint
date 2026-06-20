@echo off
echo ========================================
echo Applying Delivery Tracking Migration
echo ========================================
echo.

echo Ensuring all services are running...
docker-compose up -d

echo.
echo Waiting for database to be ready...
timeout /t 5 /nobreak >nul

echo.
echo Applying database migration...
docker-compose exec -T postgres psql -U postgres -d procurement_dss -f - < backend\add_delivery_tracking_fields.sql

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Migration applied successfully!
    echo.
    echo Restarting backend service to load new schema...
    docker-compose restart backend
    echo.
    echo ✅ Backend restarted!
    echo.
    echo 📋 New delivery tracking fields added to finalized_decisions table:
    echo    - delivery_status
    echo    - actual_delivery_date
    echo    - procurement_confirmed_at, procurement_confirmed_by_id
    echo    - is_correct_item_confirmed, serial_number
    echo    - procurement_delivery_notes
    echo    - pm_accepted_at, pm_accepted_by_id
    echo    - is_accepted_by_pm, pm_acceptance_notes
    echo    - customer_delivery_date
    echo.
    echo 🎉 Procurement Plan feature is now ready!
    echo    Navigate to "Procurement Plan" in the menu to start using it.
    echo.
) else (
    echo.
    echo ❌ Migration failed!
    echo Please check the error messages above.
    echo.
    echo Troubleshooting:
    echo 1. Ensure Docker is running
    echo 2. Check if database container is healthy: docker-compose ps
    echo 3. Check database logs: docker-compose logs db
    echo.
)

pause

