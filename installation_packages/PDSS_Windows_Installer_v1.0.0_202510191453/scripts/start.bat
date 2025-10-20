@echo off
cd /d "%~dp0"
docker-compose up -d
timeout /t 5 /nobreak >nul
start http://localhost:3000
echo PDSS started successfully
echo Opening browser...
pause
