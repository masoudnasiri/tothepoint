@echo off
echo Applying Currency Support Migration...
echo.

REM Check if Docker is running
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running. Please start Docker first.
    pause
    exit /b 1
)

REM Check if postgres service is running
docker-compose ps postgres | findstr "Up" >nul
if %errorlevel% neq 0 (
    echo ERROR: PostgreSQL service is not running. Please start the services first.
    echo Run: docker-compose up -d postgres
    pause
    exit /b 1
)

echo Applying currency support migration...
docker-compose exec -T postgres psql -U postgres -d procurement_dss -f - < backend\add_currency_support.sql

if %errorlevel% equ 0 (
    echo.
    echo ✅ Currency support migration applied successfully!
    echo.
    echo The following features have been added:
    echo - Multi-currency support with Iranian Rials as base currency
    echo - Exchange rate management
    echo - Currency conversion utilities
    echo - Updated procurement options and decisions to support currencies
    echo.
    echo Default currencies added:
    echo - IRR (Iranian Rial) - Base Currency
    echo - USD (US Dollar)
    echo - EUR (Euro)
    echo - GBP (British Pound)
    echo - JPY (Japanese Yen)
    echo - CNY (Chinese Yuan)
    echo - AED (UAE Dirham)
    echo - SAR (Saudi Riyal)
    echo - TRY (Turkish Lira)
    echo - INR (Indian Rupee)
    echo.
    echo Please restart the backend service to apply changes:
    echo docker-compose restart backend
) else (
    echo.
    echo ❌ Migration failed!
    echo Please check the error messages above.
)

echo.
pause
