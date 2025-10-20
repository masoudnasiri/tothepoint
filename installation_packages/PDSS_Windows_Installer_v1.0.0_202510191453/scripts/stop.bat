@echo off
cd /d "%~dp0\.."
docker-compose down
echo PDSS stopped successfully
pause
