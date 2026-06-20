@echo off
echo ============================================================
echo Adding Description Column to Items Master Table
echo ============================================================

docker-compose exec -T postgres psql -U postgres -d procurement_dss -c "ALTER TABLE items_master ADD COLUMN IF NOT EXISTS description TEXT;"

echo.
echo ============================================================
echo Migration completed!
echo ============================================================
echo Restarting backend...
docker-compose restart backend

echo.
echo Done! Please refresh your browser.
pause

