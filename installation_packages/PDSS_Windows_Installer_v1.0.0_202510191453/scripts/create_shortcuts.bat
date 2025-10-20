@echo off
REM Create desktop shortcuts for PDSS
set INSTALL_DIR=%~dp0..

echo Creating desktop shortcuts...

(
echo @echo off
echo cd /d "%INSTALL_DIR%"
echo docker-compose up -d
echo timeout /t 5 /nobreak ^>nul
echo start http://localhost:3000
echo echo PDSS started
) > "%USERPROFILE%\Desktop\Start PDSS.bat"

(
echo @echo off
echo cd /d "%INSTALL_DIR%"
echo docker-compose down
echo echo PDSS stopped
) > "%USERPROFILE%\Desktop\Stop PDSS.bat"

echo Desktop shortcuts created successfully
pause
