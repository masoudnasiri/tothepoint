@echo off
REM OR-Tools Enhancement Installation Script for Windows
REM This script installs the enhanced OR-Tools optimization features

echo ==================================
echo OR-Tools Enhancement Installation
echo ==================================
echo.

REM Step 1: Check if in correct directory
if not exist "backend\requirements.txt" (
    echo X Error: Please run this script from the project root directory
    exit /b 1
)

echo + Project root directory detected
echo.

REM Step 2: Install Python dependencies
echo Installing Python dependencies...
cd backend

REM Check if venv exists
if exist "venv\Scripts\activate.bat" (
    echo Virtual environment detected
    call venv\Scripts\activate.bat
)

REM Install networkx
pip install networkx==3.2.1

if %errorlevel% equ 0 (
    echo + networkx installed successfully
) else (
    echo X Failed to install networkx
    exit /b 1
)

cd ..
echo.

REM Step 3: Verify installation
echo Verifying installation...

python -c "import networkx; print('+ NetworkX version:', networkx.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo ! Warning: Could not verify networkx installation
) else (
    echo + NetworkX verified
)

python -c "import ortools; print('+ OR-Tools detected')" 2>nul
if %errorlevel% neq 0 (
    echo ! Warning: Could not verify OR-Tools installation
) else (
    echo + OR-Tools verified
)

echo.

REM Step 4: Summary
echo ==================================
echo + Installation Complete!
echo ==================================
echo.
echo Documentation Available:
echo   - OR_TOOLS_ENHANCEMENT_GUIDE.md (Comprehensive guide)
echo   - OR_TOOLS_QUICK_REFERENCE.md (Quick reference)
echo   - OR_TOOLS_IMPLEMENTATION_SUMMARY.md (Implementation details)
echo.
echo Next Steps:
echo   1. Restart your backend server:
echo      cd backend
echo      uvicorn app.main:app --reload
echo.
echo   2. Navigate to the enhanced optimization page:
echo      http://localhost:3000/optimization-enhanced
echo.
echo   3. Read the Quick Reference:
echo      type OR_TOOLS_QUICK_REFERENCE.md
echo.
echo Quick Test:
echo   - Login as admin or finance user
echo   - Go to 'Advanced Optimization' in sidebar
echo   - Click 'Run Optimization' with CP_SAT solver
echo   - Review multiple proposals
echo.
echo Happy Optimizing!
pause

