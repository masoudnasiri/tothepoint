@echo off
echo ================================================
echo  Fix Decision Factor Weights
echo ================================================
echo.
echo This will recreate the decision factor weights
echo without affecting any other data.
echo.

docker-compose exec backend python /app/reseed_weights_only.py

echo.
echo ================================================
echo.
echo Done! Please refresh your browser.
echo.
pause

