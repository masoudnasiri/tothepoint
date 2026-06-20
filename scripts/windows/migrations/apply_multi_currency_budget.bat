@echo off
echo Applying Multi-Currency Budget Migration...
echo.

docker-compose exec -T postgres psql -U postgres -d procurement_dss -f - < backend\add_multi_currency_budget.sql

if %errorlevel% equ 0 (
    echo.
    echo ✅ Multi-currency budget migration applied successfully!
    echo.
    echo Budget table now supports multiple currencies per period:
    echo - USD, EUR, GBP, IRR, AED, etc.
    echo - Example: {"USD": 1000000, "IRR": 1000000000000, "AED": 12000000000}
    echo.
    echo Please restart the backend service:
    echo docker-compose restart backend
) else (
    echo.
    echo ❌ Migration failed!
)

echo.
pause
