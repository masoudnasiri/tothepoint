@echo off
echo ============================================================
echo Adding Actual Payment Fields to Finalized Decisions Table
echo ============================================================

docker cp backend\add_actual_payment_fields.sql cahs_flow_project-postgres-1:/tmp/add_actual_payment_fields.sql
docker-compose exec -T postgres psql -U postgres -d procurement_dss -f /tmp/add_actual_payment_fields.sql

echo.
echo ============================================================
echo Migration completed!
echo ============================================================
echo Restarting backend...
docker-compose restart backend

echo.
echo Done! Please refresh your browser.
pause

