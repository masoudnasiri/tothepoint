@echo off
REM View logs for Procurement DSS

echo Viewing Procurement DSS logs...
echo Press Ctrl+C to exit
echo.

docker-compose logs -f
