@echo off
echo ========================================
echo Applying Delivery Tracking Migration
echo ========================================
echo.

echo Stopping backend service...
docker-compose stop backend

echo.
echo Applying database migration...
docker-compose exec -T db psql -U postgres -d cahs_flow_db -f /docker-entrypoint-initdb.d/add_delivery_tracking_fields.sql < backend\add_delivery_tracking_fields.sql

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Migration applied successfully!
    echo.
    echo Starting backend service...
    docker-compose up -d backend
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
) else (
    echo.
    echo ❌ Migration failed!
    echo Please check the error messages above.
    echo.
    docker-compose up -d backend
)

pause

