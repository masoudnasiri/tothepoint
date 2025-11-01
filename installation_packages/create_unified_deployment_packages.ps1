# ============================================================================
#  PDSS - Unified Deployment Package Creator
#  Creates deployment packages for BOTH Windows and Linux from Windows
#  Can run on Windows to create packages for both platforms
# ============================================================================

$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  PDSS Unified Deployment Package Creator" -ForegroundColor Cyan
Write-Host "  Creates packages for Windows AND Linux from Windows" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Package Information
$VERSION = "1.0.0"
$TIMESTAMP = Get-Date -Format "yyyyMMddHHmm"
$TIMESTAMP_FRIENDLY = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Write-Host "Version:    $VERSION" -ForegroundColor Cyan
Write-Host "Build Date: $TIMESTAMP_FRIENDLY" -ForegroundColor Cyan
Write-Host ""

################################################################################
# STAGE 1: VALIDATION
################################################################################

Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "  STAGE 1: VALIDATION" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "[1/3] Checking project structure..."
if (!(Test-Path "..\backend")) {
    Write-ColorOutput Red "[ERROR] Backend directory not found!"
    exit 1
}
if (!(Test-Path "..\frontend")) {
    Write-ColorOutput Red "[ERROR] Frontend directory not found!"
    exit 1
}
if (!(Test-Path "..\docker-compose.yml")) {
    Write-ColorOutput Red "[ERROR] docker-compose.yml not found!"
    exit 1
}
Write-ColorOutput Green "[OK] Project structure validated"
Write-Host ""

Write-Host "[2/3] Checking required files..."
if (!(Test-Path "..\backend\requirements.txt")) {
    Write-ColorOutput Red "[ERROR] Backend requirements.txt not found!"
    exit 1
}
if (!(Test-Path "..\frontend\package.json")) {
    Write-ColorOutput Red "[ERROR] Frontend package.json not found!"
    exit 1
}
Write-ColorOutput Green "[OK] Required files found"
Write-Host ""

Write-Host "[3/3] Platform detection..."
Write-ColorOutput Green "[OK] Running on Windows - Can create packages for both platforms"
Write-Host ""

################################################################################
# STAGE 2: CREATE LINUX PACKAGE
################################################################################

Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "  STAGE 2: CREATING LINUX PACKAGE" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

$LINUX_PACKAGE_NAME = "pdss-linux-v${VERSION}"
$LINUX_OUTPUT_DIR = "${LINUX_PACKAGE_NAME}"

Write-Host "[1/7] Creating Linux package directory..."
if (Test-Path "$LINUX_OUTPUT_DIR") {
    Remove-Item -Path "$LINUX_OUTPUT_DIR" -Recurse -Force
}
New-Item -ItemType Directory -Path "$LINUX_OUTPUT_DIR" -Force | Out-Null
New-Item -ItemType Directory -Path "$LINUX_OUTPUT_DIR\backend" -Force | Out-Null
New-Item -ItemType Directory -Path "$LINUX_OUTPUT_DIR\frontend" -Force | Out-Null
New-Item -ItemType Directory -Path "$LINUX_OUTPUT_DIR\docs" -Force | Out-Null
New-Item -ItemType Directory -Path "$LINUX_OUTPUT_DIR\scripts" -Force | Out-Null
New-Item -ItemType Directory -Path "$LINUX_OUTPUT_DIR\config" -Force | Out-Null
Write-ColorOutput Green "[OK] Linux directory structure created"
Write-Host ""

Write-Host "[2/7] Copying application files for Linux package..."
Copy-Item -Path "..\backend\*" -Destination "$LINUX_OUTPUT_DIR\backend\" -Recurse -Force
Get-ChildItem -Path "$LINUX_OUTPUT_DIR\backend" -Directory -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Path "$LINUX_OUTPUT_DIR\backend" -File -Recurse -Filter "*.pyc" | Remove-Item -Force

Copy-Item -Path "..\frontend\src" -Destination "$LINUX_OUTPUT_DIR\frontend\src" -Recurse -Force
Copy-Item -Path "..\frontend\public" -Destination "$LINUX_OUTPUT_DIR\frontend\public" -Recurse -Force
Copy-Item -Path "..\frontend\package.json" -Destination "$LINUX_OUTPUT_DIR\frontend\"
Copy-Item -Path "..\frontend\package-lock.json" -Destination "$LINUX_OUTPUT_DIR\frontend\" -ErrorAction SilentlyContinue
Copy-Item -Path "..\frontend\tsconfig.json" -Destination "$LINUX_OUTPUT_DIR\frontend\" -ErrorAction SilentlyContinue
Copy-Item -Path "..\frontend\Dockerfile" -Destination "$LINUX_OUTPUT_DIR\frontend\"

# Copy docker-compose.yml and update for production
Write-Host "Configuring docker-compose.yml for production (IP: 193.162.129.58)..."
$DockerComposeContent = Get-Content "..\docker-compose.yml" -Raw

# Update for production environment
$DockerComposeContent = $DockerComposeContent -replace 'ENVIRONMENT=development', 'ENVIRONMENT=production'
$DockerComposeContent = $DockerComposeContent -replace 'DEBUG=true', 'DEBUG=false'
$DockerComposeContent = $DockerComposeContent -replace 'ALLOWED_ORIGINS=\*', 'ALLOWED_ORIGINS=http://193.162.129.58:3000,http://localhost:3000'
$DockerComposeContent = $DockerComposeContent -replace 'REACT_APP_API_URL=http://backend:8000', 'REACT_APP_API_URL=http://193.162.129.58:8000'

# Save production-configured docker-compose.yml
$DockerComposeContent | Set-Content -Path "$LINUX_OUTPUT_DIR\docker-compose.yml" -Encoding UTF8
Write-ColorOutput Green "[OK] docker-compose.yml configured for production"

Copy-Item -Path "..\backend\Dockerfile" -Destination "$LINUX_OUTPUT_DIR\backend\"

Remove-Item "$LINUX_OUTPUT_DIR\frontend\node_modules" -Recurse -Force -ErrorAction SilentlyContinue
Write-ColorOutput Green "[OK] Files copied"
Write-Host ""

# Verify critical fixes are included
Write-Host "[2.5/7] Verifying critical fixes are included..."
$dockerComposePath = "$LINUX_OUTPUT_DIR\docker-compose.yml"
$configPath = "$LINUX_OUTPUT_DIR\backend\app\config.py"
$mainPath = "$LINUX_OUTPUT_DIR\backend\app\main.py"

$issues = @()

# Check docker-compose.yml
$dockerComposeContent = Get-Content $dockerComposePath -Raw
if ($dockerComposeContent -notmatch "REACT_APP_API_URL") {
    $issues += "docker-compose.yml missing REACT_APP_API_URL"
} elseif ($dockerComposeContent -notmatch "193\.162\.129\.58") {
    $issues += "docker-compose.yml REACT_APP_API_URL not set to production IP (193.162.129.58)"
}
if ($dockerComposeContent -notmatch "ALLOWED_ORIGINS") {
    $issues += "docker-compose.yml missing ALLOWED_ORIGINS"
} elseif ($dockerComposeContent -notmatch "193\.162\.129\.58.*3000") {
    $issues += "docker-compose.yml ALLOWED_ORIGINS not configured for production IP"
}
if ($dockerComposeContent -match "ENVIRONMENT=development") {
    $issues += "docker-compose.yml still configured for development (should be production)"
}
if ($dockerComposeContent -match "DEBUG=true") {
    $issues += "docker-compose.yml DEBUG still enabled (should be false for production)"
}

# Check config.py
$configContent = Get-Content $configPath -Raw -ErrorAction SilentlyContinue
if (-not $configContent) {
    $issues += "backend/app/config.py not found"
} elseif ($configContent -notmatch "get_allowed_origins") {
    $issues += "backend/app/config.py missing get_allowed_origins method"
}

# Check main.py
$mainContent = Get-Content $mainPath -Raw -ErrorAction SilentlyContinue
if (-not $mainContent) {
    $issues += "backend/app/main.py not found"
} elseif ($mainContent -notmatch "get_allowed_origins\(\)") {
    $issues += "backend/app/main.py not using get_allowed_origins()"
}

if ($issues.Count -gt 0) {
    Write-ColorOutput Yellow "[WARNING] Some fixes may be missing:"
    $issues | ForEach-Object { Write-ColorOutput Yellow "  - $_" }
} else {
    Write-ColorOutput Green "[OK] All critical fixes verified"
}
Write-Host ""

Write-Host "[3/7] Creating Linux installer script..."
$linuxInstaller = @'
#!/bin/bash
################################################################################
#  PDSS Linux Installer v1.0.0
#  Automated Installation for Linux
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo "============================================================================"
printf "  ${BOLD}Procurement Decision Support System (PDSS)${NC}\n"
echo "  Linux Installer v1.0.0"
echo "============================================================================"
echo ""

if [ "$EUID" -eq 0 ] 2>/dev/null; then 
    printf "${YELLOW}[WARNING]${NC} Running as root. Recommended to run as regular user.\n"
    echo ""
fi

echo "[1/9] Checking prerequisites..."
echo ""

if ! command -v docker >/dev/null 2>&1; then
    printf "${RED}[ERROR]${NC} Docker is not installed!\n"
    echo ""
    echo "Install Docker with:"
    echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "  sudo sh get-docker.sh"
    echo "  sudo usermod -aG docker \$USER"
    echo "  newgrp docker"
    exit 1
fi
printf "${GREEN}[OK]${NC} Docker found: $(docker --version)\n"

if ! command -v docker-compose >/dev/null 2>&1; then
    printf "${YELLOW}[WARNING]${NC} Docker Compose not found. Installing...\n"
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    printf "${GREEN}[OK]${NC} Docker Compose installed\n"
fi
printf "${GREEN}[OK]${NC} Docker Compose found: $(docker-compose --version)\n"

if ! docker ps >/dev/null 2>&1; then
    printf "${YELLOW}[WARNING]${NC} Docker daemon not running. Attempting to start...\n"
    sudo systemctl start docker || true
    sleep 5
    if ! docker ps >/dev/null 2>&1; then
        printf "${RED}[ERROR]${NC} Failed to start Docker!\n"
        exit 1
    fi
fi
printf "${GREEN}[OK]${NC} Docker daemon is running\n"
echo ""

echo "[2/9] Configuring environment..."
if [ ! -f ".env" ]; then
    cp "config/.env.example" ".env"
    printf "${GREEN}[OK]${NC} Configuration file created\n"
else
    printf "${GREEN}[OK]${NC} Using existing configuration\n"
fi
echo ""

echo "[3/9] Stopping any existing containers..."
docker-compose down >/dev/null 2>&1 || true
printf "${GREEN}[OK]${NC} Cleanup complete\n"
echo ""

echo "[4/9] Building Docker images..."
echo "This may take 5-10 minutes on first installation..."
echo ""

# Verify Dockerfiles exist
if [ ! -f "backend/Dockerfile" ]; then
    printf "${RED}[ERROR]${NC} Backend Dockerfile not found in $(pwd)/backend/Dockerfile\n"
    printf "${YELLOW}[INFO]${NC} Current directory: $(pwd)\n"
    printf "${YELLOW}[INFO]${NC} Files in current directory: $(ls -la | head -5)\n"
    exit 1
fi
if [ ! -f "frontend/Dockerfile" ]; then
    printf "${RED}[ERROR]${NC} Frontend Dockerfile not found in $(pwd)/frontend/Dockerfile\n"
    exit 1
fi

# Check internet connectivity
printf "${BLUE}[INFO]${NC} Checking internet connectivity...\n"
if ! ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1; then
    printf "${YELLOW}[WARNING]${NC} No internet connectivity detected. Docker build requires internet to pull base images.\n"
    printf "${YELLOW}[INFO]${NC} Continuing anyway - if build fails, check your network connection.\n"
else
    printf "${GREEN}[OK]${NC} Internet connectivity confirmed\n"
fi

# Pre-pull base images to avoid timeout during build
printf "${BLUE}[INFO]${NC} Pre-pulling base images...\n"
if docker pull python:3.11-slim >/dev/null 2>&1; then
    printf "${GREEN}[OK]${NC} Python base image ready\n"
else
    printf "${YELLOW}[WARNING]${NC} Failed to pre-pull python:3.11-slim - will try during build\n"
fi

if docker pull node:18-alpine >/dev/null 2>&1; then
    printf "${GREEN}[OK]${NC} Node base image ready\n"
else
    printf "${YELLOW}[WARNING]${NC} Failed to pre-pull node:18-alpine - will try during build\n"
fi

echo ""

# Build with verbose output
printf "${BLUE}[INFO]${NC} Starting Docker Compose build...\n"
if docker-compose build; then
    printf "${GREEN}[OK]${NC} Images built successfully\n"
else
    BUILD_EXIT_CODE=$?
    printf "\n${RED}[ERROR]${NC} Failed to build Docker images! (Exit code: $BUILD_EXIT_CODE)\n"
    echo ""
    printf "${YELLOW}[TROUBLESHOOTING STEPS]${NC}\n"
    echo ""
    printf "1. Check internet connectivity:\n"
    printf "   ping -c 3 registry-1.docker.io\n"
    echo ""
    printf "2. Check Docker Hub status:\n"
    printf "   Visit: https://status.docker.com\n"
    echo ""
    printf "3. Try pulling base images manually:\n"
    printf "   docker pull python:3.11-slim\n"
    printf "   docker pull node:18-alpine\n"
    echo ""
    printf "4. If behind a corporate proxy/firewall:\n"
    printf "   - Configure Docker daemon proxy: /etc/docker/daemon.json\n"
    printf "   - Set HTTP_PROXY and HTTPS_PROXY environment variables\n"
    echo ""
    printf "5. Check Docker build logs:\n"
    printf "   docker-compose build --no-cache --progress=plain\n"
    echo ""
    exit $BUILD_EXIT_CODE
fi
echo ""

echo "[5/9] Starting database..."
docker-compose up -d db
printf "${GREEN}[OK]${NC} Database started\n"
echo "Waiting for database initialization..."
sleep 15
echo ""

echo "[6/9] Starting backend service..."
docker-compose up -d backend
printf "${GREEN}[OK]${NC} Backend started\n"
echo "Waiting for backend initialization..."
sleep 20
echo ""

echo "[7/9] Starting frontend service..."
docker-compose up -d frontend
printf "${GREEN}[OK]${NC} Frontend started\n"
echo "Waiting for frontend initialization..."
sleep 25
echo ""

echo "[8/9] Verifying installation..."
docker-compose ps
echo ""

echo "[9/9] Creating management scripts..."
INSTALL_DIR="$(pwd)"

cat > "$HOME/pdss-start.sh" << EOFSTART
#!/bin/bash
cd "$INSTALL_DIR"
docker-compose up -d
sleep 5
echo "PDSS started successfully!"
xdg-open http://localhost:3000 >/dev/null 2>&1 || echo "Access at: http://localhost:3000"
EOFSTART
chmod +x "$HOME/pdss-start.sh"

cat > "$HOME/pdss-stop.sh" << EOFSTOP
#!/bin/bash
cd "$INSTALL_DIR"
docker-compose down
echo "PDSS stopped successfully!"
EOFSTOP
chmod +x "$HOME/pdss-stop.sh"

printf "${GREEN}[OK]${NC} Management scripts created\n"
echo ""

echo "============================================================================"
printf "  ${BOLD}INSTALLATION COMPLETE!${NC}\n"
echo "============================================================================"
echo ""
echo "Access URL: http://localhost:3000"
echo ""
echo "Default Login Credentials:"
echo "  Admin:       admin / admin123"
echo "  Finance:     finance1 / finance123"
echo "  PM:          pm1 / pm123"
echo "  Procurement: proc1 / proc123"
echo ""
printf "${YELLOW}IMPORTANT: Change default passwords after first login!${NC}\n"
echo ""
echo "Management Scripts:"
echo "  $HOME/pdss-start.sh   - Start PDSS"
echo "  $HOME/pdss-stop.sh    - Stop PDSS"
echo ""
echo "============================================================================"
'@

# Save with Unix line endings (LF only, no BOM)
# Remove all CRLF and ensure only LF
$cleanScript = $linuxInstaller -replace "`r`n", "`n" -replace "`r", "`n"
# Use UTF8NoBOM encoding and ensure LF line endings
[System.IO.File]::WriteAllText("$LINUX_OUTPUT_DIR\install.sh", $cleanScript, [System.Text.UTF8Encoding]::new($false))
Write-ColorOutput Green "[OK] Linux installer created (Unix line endings)"
Write-Host ""

Write-Host "[4/7] Creating Linux management scripts..."
$startScript = @'
#!/bin/bash
cd "$(dirname "$0")/.."
docker-compose up -d
sleep 5
echo "PDSS started successfully!"
xdg-open http://localhost:3000 >/dev/null 2>&1 || echo "Access at: http://localhost:3000"
'@

$stopScript = @'
#!/bin/bash
cd "$(dirname "$0")/.."
docker-compose down
echo "PDSS stopped successfully!"
'@

$statusScript = @'
#!/bin/bash
cd "$(dirname "$0")/.."
echo "========================================================================"
echo "  PDSS System Status"
echo "========================================================================"
docker-compose ps
'@

$restartScript = @'
#!/bin/bash
cd "$(dirname "$0")/.."
echo "Restarting PDSS..."
docker-compose restart
echo "PDSS restarted successfully!"
'@

# Save all scripts with proper Unix line endings (LF only, no BOM)
[System.IO.File]::WriteAllText("$LINUX_OUTPUT_DIR\scripts\start.sh", ($startScript -replace "`r`n", "`n" -replace "`r", "`n"), [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText("$LINUX_OUTPUT_DIR\scripts\stop.sh", ($stopScript -replace "`r`n", "`n" -replace "`r", "`n"), [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText("$LINUX_OUTPUT_DIR\scripts\status.sh", ($statusScript -replace "`r`n", "`n" -replace "`r", "`n"), [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText("$LINUX_OUTPUT_DIR\scripts\restart.sh", ($restartScript -replace "`r`n", "`n" -replace "`r", "`n"), [System.Text.UTF8Encoding]::new($false))

Write-ColorOutput Green "[OK] Linux management scripts created"
Write-Host ""

Write-Host "[5/7] Copying documentation and config..."
if (Test-Path "..\README.md") { Copy-Item "..\README.md" "$LINUX_OUTPUT_DIR\docs\README.md" }
if (Test-Path "config_template.env") {
    Copy-Item "config_template.env" "$LINUX_OUTPUT_DIR\config\.env.example"
} else {
    @"
# PDSS Configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/procurement_dss
SECRET_KEY=change-this-secret-key-in-production
ALLOWED_ORIGINS=http://localhost:3000
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_DB=procurement_dss
"@ | Out-File -FilePath "$LINUX_OUTPUT_DIR\config\.env.example" -Encoding UTF8
}
Write-ColorOutput Green "[OK] Documentation and config copied"
Write-Host ""

Write-Host "[6/7] Creating Linux README..."
$linuxReadme = @"
========================================================================
  PROCUREMENT DECISION SUPPORT SYSTEM (PDSS)
  Linux Installation Package v$VERSION
========================================================================

BUILD INFORMATION:
  Version: $VERSION
  Build Date: $TIMESTAMP_FRIENDLY
  Platform: Linux

SYSTEM REQUIREMENTS:
  - Linux (Ubuntu 18.04+, Debian 10+, CentOS 7+, RHEL 7+)
  - Docker Engine 20.10+
  - Docker Compose 1.29+
  - 4GB RAM minimum (8GB recommended)
  - 10GB free disk space

INSTALLATION:
  1. Run: chmod +x install.sh
  2. Run: sudo ./install.sh
  3. Access: http://localhost:3000

MANAGEMENT SCRIPTS:
  scripts/start.sh     - Start PDSS
  scripts/stop.sh      - Stop PDSS
  scripts/status.sh     - Check status
  scripts/restart.sh    - Restart PDSS

DEFAULT CREDENTIALS:
  Admin: admin / admin123
  Finance: finance1 / finance123
  PM: pm1 / pm123
  Procurement: proc1 / proc123

========================================================================
"@
$linuxReadme | Out-File -FilePath "$LINUX_OUTPUT_DIR\README.txt" -Encoding UTF8
Write-ColorOutput Green "[OK] Linux README created"
Write-Host ""

Write-Host "[7/7] Creating Linux ZIP archive..."
$LINUX_ZIP_NAME = "${LINUX_PACKAGE_NAME}-${TIMESTAMP}.zip"
Compress-Archive -Path "$LINUX_OUTPUT_DIR\*" -DestinationPath $LINUX_ZIP_NAME -Force
$LINUX_ZIP_SIZE = [math]::Round((Get-Item $LINUX_ZIP_NAME).Length / 1MB, 2)
Write-ColorOutput Green "[OK] Linux ZIP created: $LINUX_ZIP_NAME ($LINUX_ZIP_SIZE MB)"
Write-Host ""

################################################################################
# STAGE 3: CREATE WINDOWS PACKAGE
################################################################################

Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "  STAGE 3: CREATING WINDOWS PACKAGE" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

$WINDOWS_PACKAGE_NAME = "PDSS_Windows_v${VERSION}"
$WINDOWS_OUTPUT_DIR = "${WINDOWS_PACKAGE_NAME}_${TIMESTAMP}"

Write-Host "[1/7] Creating Windows package directory..."
if (Test-Path "$WINDOWS_OUTPUT_DIR") {
    Remove-Item -Path "$WINDOWS_OUTPUT_DIR" -Recurse -Force
}
New-Item -ItemType Directory -Path "$WINDOWS_OUTPUT_DIR" -Force | Out-Null
New-Item -ItemType Directory -Path "$WINDOWS_OUTPUT_DIR\backend" -Force | Out-Null
New-Item -ItemType Directory -Path "$WINDOWS_OUTPUT_DIR\frontend" -Force | Out-Null
New-Item -ItemType Directory -Path "$WINDOWS_OUTPUT_DIR\docs" -Force | Out-Null
New-Item -ItemType Directory -Path "$WINDOWS_OUTPUT_DIR\scripts" -Force | Out-Null
New-Item -ItemType Directory -Path "$WINDOWS_OUTPUT_DIR\config" -Force | Out-Null
Write-ColorOutput Green "[OK] Windows directory structure created"
Write-Host ""

Write-Host "[2/7] Copying application files for Windows package..."
Copy-Item -Path "..\backend\*" -Destination "$WINDOWS_OUTPUT_DIR\backend\" -Recurse -Force
Get-ChildItem -Path "$WINDOWS_OUTPUT_DIR\backend" -Directory -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Path "$WINDOWS_OUTPUT_DIR\backend" -File -Recurse -Filter "*.pyc" | Remove-Item -Force

Copy-Item -Path "..\frontend\src" -Destination "$WINDOWS_OUTPUT_DIR\frontend\src" -Recurse -Force
Copy-Item -Path "..\frontend\public" -Destination "$WINDOWS_OUTPUT_DIR\frontend\public" -Recurse -Force
Copy-Item -Path "..\frontend\package.json" -Destination "$WINDOWS_OUTPUT_DIR\frontend\"
Copy-Item -Path "..\frontend\package-lock.json" -Destination "$WINDOWS_OUTPUT_DIR\frontend\" -ErrorAction SilentlyContinue
Copy-Item -Path "..\frontend\tsconfig.json" -Destination "$WINDOWS_OUTPUT_DIR\frontend\" -ErrorAction SilentlyContinue
Copy-Item -Path "..\frontend\Dockerfile" -Destination "$WINDOWS_OUTPUT_DIR\frontend\"

# Copy docker-compose.yml and update for production (Windows package)
Write-Host "Configuring docker-compose.yml for production (IP: 193.162.129.58)..."
$DockerComposeContentWin = Get-Content "..\docker-compose.yml" -Raw

# Update for production environment
$DockerComposeContentWin = $DockerComposeContentWin -replace 'ENVIRONMENT=development', 'ENVIRONMENT=production'
$DockerComposeContentWin = $DockerComposeContentWin -replace 'DEBUG=true', 'DEBUG=false'
$DockerComposeContentWin = $DockerComposeContentWin -replace 'ALLOWED_ORIGINS=\*', 'ALLOWED_ORIGINS=http://193.162.129.58:3000,http://localhost:3000'
$DockerComposeContentWin = $DockerComposeContentWin -replace 'REACT_APP_API_URL=http://backend:8000', 'REACT_APP_API_URL=http://193.162.129.58:8000'

# Save production-configured docker-compose.yml
$DockerComposeContentWin | Set-Content -Path "$WINDOWS_OUTPUT_DIR\docker-compose.yml" -Encoding UTF8
Write-ColorOutput Green "[OK] docker-compose.yml configured for production"

Copy-Item -Path "..\backend\Dockerfile" -Destination "$WINDOWS_OUTPUT_DIR\backend\"

Remove-Item "$WINDOWS_OUTPUT_DIR\frontend\node_modules" -Recurse -Force -ErrorAction SilentlyContinue
Write-ColorOutput Green "[OK] Files copied"
Write-Host ""

# Verify critical fixes are included (Windows package)
Write-Host "[2.5/7] Verifying critical fixes are included (Windows)..."
$dockerComposePathWin = "$WINDOWS_OUTPUT_DIR\docker-compose.yml"
$configPathWin = "$WINDOWS_OUTPUT_DIR\backend\app\config.py"
$mainPathWin = "$WINDOWS_OUTPUT_DIR\backend\app\main.py"

$issuesWin = @()

# Check docker-compose.yml
$dockerComposeContentWin = Get-Content $dockerComposePathWin -Raw
if ($dockerComposeContentWin -notmatch "REACT_APP_API_URL") {
    $issuesWin += "docker-compose.yml missing REACT_APP_API_URL"
} elseif ($dockerComposeContentWin -notmatch "193\.162\.129\.58") {
    $issuesWin += "docker-compose.yml REACT_APP_API_URL not set to production IP (193.162.129.58)"
}
if ($dockerComposeContentWin -notmatch "ALLOWED_ORIGINS") {
    $issuesWin += "docker-compose.yml missing ALLOWED_ORIGINS"
} elseif ($dockerComposeContentWin -notmatch "193\.162\.129\.58.*3000") {
    $issuesWin += "docker-compose.yml ALLOWED_ORIGINS not configured for production IP"
}
if ($dockerComposeContentWin -match "ENVIRONMENT=development") {
    $issuesWin += "docker-compose.yml still configured for development (should be production)"
}
if ($dockerComposeContentWin -match "DEBUG=true") {
    $issuesWin += "docker-compose.yml DEBUG still enabled (should be false for production)"
}

# Check config.py
$configContentWin = Get-Content $configPathWin -Raw -ErrorAction SilentlyContinue
if (-not $configContentWin) {
    $issuesWin += "backend/app/config.py not found"
} elseif ($configContentWin -notmatch "get_allowed_origins") {
    $issuesWin += "backend/app/config.py missing get_allowed_origins method"
}

# Check main.py
$mainContentWin = Get-Content $mainPathWin -Raw -ErrorAction SilentlyContinue
if (-not $mainContentWin) {
    $issuesWin += "backend/app/main.py not found"
} elseif ($mainContentWin -notmatch "get_allowed_origins\(\)") {
    $issuesWin += "backend/app/main.py not using get_allowed_origins()"
}

if ($issuesWin.Count -gt 0) {
    Write-ColorOutput Yellow "[WARNING] Some fixes may be missing:"
    $issuesWin | ForEach-Object { Write-ColorOutput Yellow "  - $_" }
} else {
    Write-ColorOutput Green "[OK] All critical fixes verified"
}
Write-Host ""

Write-Host "[3/7] Creating Windows installer script..."
$windowsInstaller = @"
@echo off
REM ========================================================================
REM  PDSS Windows Installer v$VERSION
REM ========================================================================

echo.
echo ========================================================================
echo   Procurement Decision Support System (PDSS)
echo   Windows Installer v$VERSION
echo ========================================================================
echo.

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Administrator privileges required!
    echo Please right-click and select "Run as Administrator"
    pause
    exit /b 1
)

echo [1/8] Checking prerequisites...
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Docker Desktop is not installed!
    echo Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo [OK] Docker Desktop found

docker ps >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Docker Desktop is not running!
    pause
    exit /b 1
)
echo [OK] Docker is running
echo.

echo [2/8] Configuring environment...
if not exist ".env" (
    copy "config\.env.example" ".env" >nul 2>&1
    echo [OK] Configuration file created
) else (
    echo [OK] Using existing configuration
)
echo.

echo [3/8] Stopping any existing containers...
docker-compose down >nul 2>&1
echo [OK] Cleanup complete
echo.

echo [4/8] Building Docker images...
echo This may take 5-10 minutes...
docker-compose build
if %errorLevel% neq 0 (
    echo [ERROR] Failed to build Docker images!
    pause
    exit /b 1
)
echo [OK] Images built successfully
echo.

echo [5/8] Starting database...
docker-compose up -d db
timeout /t 15 /nobreak >nul
echo [OK] Database started
echo.

echo [6/8] Starting backend service...
docker-compose up -d backend
timeout /t 20 /nobreak >nul
echo [OK] Backend started
echo.

echo [7/8] Starting frontend service...
docker-compose up -d frontend
timeout /t 25 /nobreak >nul
echo [OK] Frontend started
echo.

echo [8/8] Verifying installation...
docker-compose ps
echo.

echo ========================================================================
echo   INSTALLATION COMPLETE!
echo ========================================================================
echo.
echo Access URL: http://localhost:3000
echo.
echo Default Login Credentials:
echo   Admin: admin / admin123
echo   Finance: finance1 / finance123
echo   PM: pm1 / pm123
echo   Procurement: proc1 / proc123
echo.
echo IMPORTANT: Change default passwords after first login!
echo.
timeout /t 3 /nobreak >nul
start http://localhost:3000
pause
"@
$windowsInstaller | Out-File -FilePath "$WINDOWS_OUTPUT_DIR\INSTALL.bat" -Encoding ASCII
Write-ColorOutput Green "[OK] Windows installer created"
Write-Host ""

Write-Host "[4/7] Creating Windows management scripts..."
$windowsStartScript = @'
@echo off
cd /d "%~dp0\.."
docker-compose up -d
timeout /t 5 /nobreak >nul
start http://localhost:3000
echo PDSS started successfully!
pause
'@

$windowsStopScript = @'
@echo off
cd /d "%~dp0\.."
docker-compose down
echo PDSS stopped successfully!
pause
'@

$windowsStatusScript = @'
@echo off
cd /d "%~dp0\.."
echo ========================================================================
echo   PDSS System Status
echo ========================================================================
docker-compose ps
pause
'@

$windowsRestartScript = @'
@echo off
cd /d "%~dp0\.."
echo Restarting PDSS...
docker-compose restart
echo PDSS restarted successfully!
pause
'@

$windowsStartScript | Out-File -FilePath "$WINDOWS_OUTPUT_DIR\scripts\start.bat" -Encoding ASCII
$windowsStopScript | Out-File -FilePath "$WINDOWS_OUTPUT_DIR\scripts\stop.bat" -Encoding ASCII
$windowsStatusScript | Out-File -FilePath "$WINDOWS_OUTPUT_DIR\scripts\status.bat" -Encoding ASCII
$windowsRestartScript | Out-File -FilePath "$WINDOWS_OUTPUT_DIR\scripts\restart.bat" -Encoding ASCII
Write-ColorOutput Green "[OK] Windows management scripts created"
Write-Host ""

Write-Host "[5/7] Copying documentation and config..."
if (Test-Path "..\README.md") { Copy-Item "..\README.md" "$WINDOWS_OUTPUT_DIR\docs\README.md" }
if (Test-Path "config_template.env") {
    Copy-Item "config_template.env" "$WINDOWS_OUTPUT_DIR\config\.env.example"
} else {
    @"
# PDSS Configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/procurement_dss
SECRET_KEY=change-this-secret-key-in-production
ALLOWED_ORIGINS=http://localhost:3000
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_DB=procurement_dss
"@ | Out-File -FilePath "$WINDOWS_OUTPUT_DIR\config\.env.example" -Encoding UTF8
}
Write-ColorOutput Green "[OK] Documentation and config copied"
Write-Host ""

Write-Host "[6/7] Creating Windows README..."
$windowsReadme = @"
========================================================================
  PROCUREMENT DECISION SUPPORT SYSTEM (PDSS)
  Windows Installation Package v$VERSION
========================================================================

BUILD INFORMATION:
  Version: $VERSION
  Build Date: $TIMESTAMP_FRIENDLY
  Platform: Windows

SYSTEM REQUIREMENTS:
  - Windows 10/11 or Windows Server 2019+
  - Docker Desktop for Windows
  - 4GB RAM minimum (8GB recommended)
  - 10GB free disk space

INSTALLATION:
  1. Ensure Docker Desktop is installed and running
  2. Right-click INSTALL.bat and select "Run as Administrator"
  3. Follow the on-screen instructions
  4. Access: http://localhost:3000

MANAGEMENT SCRIPTS:
  scripts\start.bat      - Start PDSS
  scripts\stop.bat       - Stop PDSS
  scripts\status.bat     - Check status
  scripts\restart.bat    - Restart PDSS

DEFAULT CREDENTIALS:
  Admin: admin / admin123
  Finance: finance1 / finance123
  PM: pm1 / pm123
  Procurement: proc1 / proc123

========================================================================
"@
$windowsReadme | Out-File -FilePath "$WINDOWS_OUTPUT_DIR\README.txt" -Encoding UTF8
Write-ColorOutput Green "[OK] Windows README created"
Write-Host ""

Write-Host "[7/7] Creating Windows ZIP archive..."
$WINDOWS_ZIP_NAME = "${WINDOWS_PACKAGE_NAME}_${TIMESTAMP}.zip"
Compress-Archive -Path "$WINDOWS_OUTPUT_DIR\*" -DestinationPath $WINDOWS_ZIP_NAME -Force
$WINDOWS_ZIP_SIZE = [math]::Round((Get-Item $WINDOWS_ZIP_NAME).Length / 1MB, 2)
Write-ColorOutput Green "[OK] Windows ZIP created: $WINDOWS_ZIP_NAME ($WINDOWS_ZIP_SIZE MB)"
Write-Host ""

################################################################################
# FINAL SUMMARY
################################################################################

Write-Host "============================================================================" -ForegroundColor Green
Write-Host "  BUILD COMPLETE!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Packages Created:" -ForegroundColor Cyan
Write-Host "  Linux:  $LINUX_OUTPUT_DIR" 
Write-Host "  Linux ZIP:  $LINUX_ZIP_NAME ($LINUX_ZIP_SIZE MB)"
Write-Host "  Windows: $WINDOWS_OUTPUT_DIR"
Write-Host "  Windows ZIP: $WINDOWS_ZIP_NAME ($WINDOWS_ZIP_SIZE MB)"
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  Linux Deployment:"
Write-Host "    1. Transfer $LINUX_ZIP_NAME to Linux server"
Write-Host "    2. Extract: unzip $LINUX_ZIP_NAME"
Write-Host "    3. Run: cd $LINUX_OUTPUT_DIR && chmod +x install.sh && sudo ./install.sh"
Write-Host ""
Write-Host "  Windows Deployment:"
Write-Host "    1. Transfer $WINDOWS_ZIP_NAME to Windows server"
Write-Host "    2. Extract the ZIP file"
Write-Host "    3. Right-click INSTALL.bat and select `"Run as Administrator`""
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""

