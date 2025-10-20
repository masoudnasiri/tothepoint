@echo off
cd /d "%~dp0\.."
echo Restarting PDSS...
docker-compose restart
echo PDSS restarted successfully
pause
