# ============================================================================
#  PDSS - Linux Installation Package Creator (PowerShell Version)
#  Creates complete Linux installation packages from Windows
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
Write-Host "  PDSS Linux Installation Package Creator" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Package Information
$VERSION = "1.0.0"
$PACKAGE_NAME = "pdss"
$FULL_NAME = "Procurement Decision Support System"
$TIMESTAMP = Get-Date -Format "yyyyMMddHHmm"
$TIMESTAMP_FRIENDLY = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
# Use simple directory name to avoid Docker naming issues
$OUTPUT_DIR = "${PACKAGE_NAME}-linux-v${VERSION}"
$ARCHIVE_NAME = "${PACKAGE_NAME}-linux-v${VERSION}-${TIMESTAMP}"
$TARBALL_NAME = "${ARCHIVE_NAME}.tar.gz"
$ZIP_NAME = "${ARCHIVE_NAME}.zip"

Write-Host "Version:    $VERSION" -ForegroundColor Cyan
Write-Host "Build Date: $TIMESTAMP_FRIENDLY" -ForegroundColor Cyan
Write-Host "Package:    $OUTPUT_DIR" -ForegroundColor Cyan
Write-Host ""

################################################################################
# STAGE 1: PRE-BUILD VALIDATION
################################################################################

Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "  STAGE 1: PRE-BUILD VALIDATION" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "[1/5] Checking project structure..."
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

Write-Host "[2/5] Checking required files..."
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

Write-Host "[3/5] Creating package directory structure..."
# Remove old package directory if exists
if (Test-Path "$OUTPUT_DIR") {
    Write-Host "      Removing existing package directory..."
    Remove-Item -Path "$OUTPUT_DIR" -Recurse -Force
}
New-Item -ItemType Directory -Path "$OUTPUT_DIR" -Force | Out-Null
New-Item -ItemType Directory -Path "$OUTPUT_DIR\backend" -Force | Out-Null
New-Item -ItemType Directory -Path "$OUTPUT_DIR\frontend" -Force | Out-Null
New-Item -ItemType Directory -Path "$OUTPUT_DIR\docs" -Force | Out-Null
New-Item -ItemType Directory -Path "$OUTPUT_DIR\scripts" -Force | Out-Null
New-Item -ItemType Directory -Path "$OUTPUT_DIR\config" -Force | Out-Null
New-Item -ItemType Directory -Path "$OUTPUT_DIR\systemd" -Force | Out-Null
Write-ColorOutput Green "[OK] Directory structure created"
Write-Host ""

Write-Host "[4/5] Generating package metadata..."
@"
Package: $FULL_NAME (PDSS)
Version: $VERSION
Build Date: $TIMESTAMP_FRIENDLY
Platform: Linux (Ubuntu/Debian/CentOS/RHEL)

Components:
- Backend: FastAPI + PostgreSQL
- Frontend: React + TypeScript
- Deployment: Docker + Docker Compose

System Requirements:
- Linux (Ubuntu 18.04+, Debian 10+, CentOS 7+, RHEL 7+)
- Docker Engine 20.10+
- Docker Compose 1.29+
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space

Build Information:
- Build ID: $TIMESTAMP
- Package Size: (calculated after build)
"@ | Out-File -FilePath "$OUTPUT_DIR\PACKAGE_INFO.txt" -Encoding UTF8
Write-ColorOutput Green "[OK] Metadata generated"
Write-Host ""

Write-Host "[5/5] Creating version file..."
@"
{
  "version": "$VERSION",
  "build": "$TIMESTAMP",
  "platform": "linux",
  "created": "$TIMESTAMP_FRIENDLY"
}
"@ | Out-File -FilePath "$OUTPUT_DIR\version.json" -Encoding UTF8
Write-ColorOutput Green "[OK] Version file created"
Write-Host ""

################################################################################
# STAGE 2: COPYING APPLICATION FILES
################################################################################

Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "  STAGE 2: COPYING APPLICATION FILES" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "[1/5] Copying backend application..."
Copy-Item -Path "..\backend\*" -Destination "$OUTPUT_DIR\backend\" -Recurse -Force
Write-ColorOutput Green "[OK] Backend copied"

Write-Host "      Cleaning Python cache..."
Get-ChildItem -Path "$OUTPUT_DIR\backend" -Directory -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Path "$OUTPUT_DIR\backend" -File -Recurse -Filter "*.pyc" | Remove-Item -Force
Remove-Item "$OUTPUT_DIR\backend\.dockerignore" -ErrorAction SilentlyContinue
Remove-Item "$OUTPUT_DIR\backend\.gitignore" -ErrorAction SilentlyContinue
Write-Host "      [OK] Cleanup complete" -ForegroundColor Green
Write-Host ""

Write-Host "[2/5] Copying frontend application..."
Copy-Item -Path "..\frontend\src" -Destination "$OUTPUT_DIR\frontend\src" -Recurse -Force
Copy-Item -Path "..\frontend\public" -Destination "$OUTPUT_DIR\frontend\public" -Recurse -Force
Copy-Item -Path "..\frontend\package.json" -Destination "$OUTPUT_DIR\frontend\"
Copy-Item -Path "..\frontend\package-lock.json" -Destination "$OUTPUT_DIR\frontend\" -ErrorAction SilentlyContinue
Copy-Item -Path "..\frontend\tsconfig.json" -Destination "$OUTPUT_DIR\frontend\" -ErrorAction SilentlyContinue
Copy-Item -Path "..\frontend\.env.example" -Destination "$OUTPUT_DIR\frontend\" -ErrorAction SilentlyContinue
Copy-Item -Path "..\frontend\Dockerfile" -Destination "$OUTPUT_DIR\frontend\"
Write-ColorOutput Green "[OK] Frontend copied"

Remove-Item "$OUTPUT_DIR\frontend\node_modules" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$OUTPUT_DIR\frontend\.gitignore" -ErrorAction SilentlyContinue
Write-Host ""

Write-Host "[3/5] Copying Docker configuration..."
Copy-Item -Path "..\docker-compose.yml" -Destination "$OUTPUT_DIR\"
Copy-Item -Path "..\backend\Dockerfile" -Destination "$OUTPUT_DIR\backend\"
Copy-Item -Path "..\frontend\Dockerfile" -Destination "$OUTPUT_DIR\frontend\"
Write-ColorOutput Green "[OK] Docker files copied"
Write-Host ""

Write-Host "[4/5] Copying documentation..."
if (Test-Path "..\README.md") { Copy-Item "..\README.md" "$OUTPUT_DIR\docs\README.md" }
if (Test-Path "..\USER_GUIDE.md") { Copy-Item "..\USER_GUIDE.md" "$OUTPUT_DIR\docs\USER_GUIDE.md" }
if (Test-Path "..\COMPLETE_SYSTEM_DOCUMENTATION.md") { Copy-Item "..\COMPLETE_SYSTEM_DOCUMENTATION.md" "$OUTPUT_DIR\docs\" }

if (!(Test-Path "$OUTPUT_DIR\docs\README.md") -and (Test-Path "README.md")) { Copy-Item "README.md" "$OUTPUT_DIR\docs\" }
if (!(Test-Path "$OUTPUT_DIR\docs\USER_GUIDE.md") -and (Test-Path "USER_GUIDE.md")) { Copy-Item "USER_GUIDE.md" "$OUTPUT_DIR\docs\" }
if (Test-Path "INSTALLATION_GUIDE.md") { Copy-Item "INSTALLATION_GUIDE.md" "$OUTPUT_DIR\docs\" }
if (Test-Path "SYSTEM_REQUIREMENTS.md") { Copy-Item "SYSTEM_REQUIREMENTS.md" "$OUTPUT_DIR\docs\" }
if (Test-Path "QUICK_START.md") { Copy-Item "QUICK_START.md" "$OUTPUT_DIR\docs\" }
Write-ColorOutput Green "[OK] Documentation copied"
Write-Host ""

Write-Host "[5/5] Copying configuration templates..."
if (Test-Path "config_template.env") {
    Copy-Item "config_template.env" "$OUTPUT_DIR\config\.env.example"
} else {
    @"
# PDSS Configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/procurement_dss
SECRET_KEY=change-this-secret-key-in-production
ALLOWED_ORIGINS=http://localhost:3000
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=procurement_dss
"@ | Out-File -FilePath "$OUTPUT_DIR\config\.env.example" -Encoding UTF8
}
Write-ColorOutput Green "[OK] Configuration templates copied"
Write-Host ""

################################################################################
# STAGE 3: CREATING INSTALLATION SCRIPTS
################################################################################

Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "  STAGE 3: CREATING INSTALLATION SCRIPTS" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "[1/5] Creating main installer script..."
# Read the installer script from the .sh version we created
if (Test-Path "create_linux_installer_package.sh") {
    # Extract the installer script content from the shell script
    $installerContent = @'
#!/bin/bash
################################################################################
#  PDSS Linux Installer
#  Automated Installation for Linux
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo "============================================================================"
echo -e "  ${BOLD}Procurement Decision Support System (PDSS)${NC}"
echo "  Linux Installer v1.0.0"
echo "============================================================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${YELLOW}[WARNING]${NC} Running as root. Recommended to run as regular user."
    echo ""
fi

echo "[1/9] Checking prerequisites..."
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker is not installed!"
    echo ""
    echo "Install Docker with:"
    echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "  sudo sh get-docker.sh"
    echo "  sudo usermod -aG docker \$USER"
    echo "  newgrp docker"
    echo ""
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Docker found: $(docker --version)"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} Docker Compose not found. Installing..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}[OK]${NC} Docker Compose installed"
fi
echo -e "${GREEN}[OK]${NC} Docker Compose found: $(docker-compose --version)"

# Check if Docker daemon is running
if ! docker ps &> /dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} Docker daemon not running. Attempting to start..."
    sudo systemctl start docker || true
    sleep 5
    
    if ! docker ps &> /dev/null; then
        echo -e "${RED}[ERROR]${NC} Failed to start Docker!"
        echo "Please start Docker manually: sudo systemctl start docker"
        exit 1
    fi
fi
echo -e "${GREEN}[OK]${NC} Docker daemon is running"
echo ""

echo "[2/9] Configuring environment..."
if [ ! -f ".env" ]; then
    cp "config/.env.example" ".env"
    echo -e "${GREEN}[OK]${NC} Configuration file created"
else
    echo -e "${GREEN}[OK]${NC} Using existing configuration"
fi
echo ""

echo "[3/9] Stopping any existing containers..."
docker-compose down &> /dev/null || true
echo -e "${GREEN}[OK]${NC} Cleanup complete"
echo ""

echo "[4/9] Building Docker images..."
echo "This may take 5-10 minutes on first installation..."
if ! docker-compose build; then
    echo -e "${RED}[ERROR]${NC} Failed to build Docker images!"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Images built successfully"
echo ""

echo "[5/9] Starting database..."
docker-compose up -d db
echo -e "${GREEN}[OK]${NC} Database started"
echo "Waiting for database initialization..."
sleep 15
echo ""

echo "[6/9] Starting backend service..."
docker-compose up -d backend
echo -e "${GREEN}[OK]${NC} Backend started"
echo "Waiting for backend initialization..."
sleep 20
echo ""

echo "[7/9] Starting frontend service..."
docker-compose up -d frontend
echo -e "${GREEN}[OK]${NC} Frontend started"
echo "Waiting for frontend initialization..."
sleep 25
echo ""

echo "[8/9] Verifying installation..."
docker-compose ps
echo ""

echo "[9/9] Creating management scripts..."
INSTALL_DIR="$(pwd)"

# Create start script
cat > "$HOME/pdss-start.sh" << EOFSTART
#!/bin/bash
cd "$INSTALL_DIR"
docker-compose up -d
sleep 5
echo "PDSS started successfully!"
xdg-open http://localhost:3000 2>/dev/null || echo "Access at: http://localhost:3000"
EOFSTART
chmod +x "$HOME/pdss-start.sh"

# Create stop script
cat > "$HOME/pdss-stop.sh" << EOFSTOP
#!/bin/bash
cd "$INSTALL_DIR"
docker-compose down
echo "PDSS stopped successfully!"
EOFSTOP
chmod +x "$HOME/pdss-stop.sh"

echo -e "${GREEN}[OK]${NC} Management scripts created"
echo ""

echo "============================================================================"
echo -e "  ${BOLD}INSTALLATION COMPLETE!${NC}"
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
echo -e "${YELLOW}IMPORTANT: Change default passwords after first login!${NC}"
echo ""
echo "Management Scripts:"
echo "  $HOME/pdss-start.sh   - Start PDSS"
echo "  $HOME/pdss-stop.sh    - Stop PDSS"
echo ""
echo "============================================================================"
'@
    
    # Save with Unix line endings (LF) instead of Windows (CRLF)
    $installerContent -replace "`r`n", "`n" | Out-File -FilePath "$OUTPUT_DIR\install.sh" -Encoding UTF8 -NoNewline
}
Write-ColorOutput Green "[OK] Main installer created (Unix line endings)"
Write-Host ""

Write-Host "[2/5] Creating management scripts..."

# Start script
$startScript = @'
#!/bin/bash
cd "$(dirname "$0")/.."
docker-compose up -d
sleep 5
echo "PDSS started successfully!"
xdg-open http://localhost:3000 2>/dev/null || echo "Access at: http://localhost:3000"
'@
$startScript -replace "`r`n", "`n" | Out-File -FilePath "$OUTPUT_DIR\scripts\start.sh" -Encoding UTF8 -NoNewline

# Stop script
$stopScript = @'
#!/bin/bash
cd "$(dirname "$0")/.."
docker-compose down
echo "PDSS stopped successfully!"
'@
$stopScript -replace "`r`n", "`n" | Out-File -FilePath "$OUTPUT_DIR\scripts\stop.sh" -Encoding UTF8 -NoNewline

# Status script
$statusScript = @'
#!/bin/bash
cd "$(dirname "$0")/.."
echo "========================================================================"
echo "  PDSS System Status"
echo "========================================================================"
echo ""
docker-compose ps
echo ""
'@
$statusScript -replace "`r`n", "`n" | Out-File -FilePath "$OUTPUT_DIR\scripts\status.sh" -Encoding UTF8 -NoNewline

# Logs script
$logsScript = @'
#!/bin/bash
cd "$(dirname "$0")/.."
docker-compose logs -f
'@
$logsScript -replace "`r`n", "`n" | Out-File -FilePath "$OUTPUT_DIR\scripts\logs.sh" -Encoding UTF8 -NoNewline

# Restart script
$restartScript = @'
#!/bin/bash
cd "$(dirname "$0")/.."
echo "Restarting PDSS..."
docker-compose restart
echo "PDSS restarted successfully!"
'@
$restartScript -replace "`r`n", "`n" | Out-File -FilePath "$OUTPUT_DIR\scripts\restart.sh" -Encoding UTF8 -NoNewline

# Backup script
$backupScript = @'
#!/bin/bash
cd "$(dirname "$0")/.."
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "Creating database backup..."
docker-compose exec -T db pg_dump -U postgres procurement_dss > "$BACKUP_DIR/db_backup_$DATE.sql"

echo "Backup saved: $BACKUP_DIR/db_backup_$DATE.sql"

# Keep only last 30 days
find "$BACKUP_DIR" -name "*.sql" -mtime +30 -delete
'@
$backupScript -replace "`r`n", "`n" | Out-File -FilePath "$OUTPUT_DIR\scripts\backup.sh" -Encoding UTF8 -NoNewline

# Uninstall script
$uninstallScript = @'
#!/bin/bash
cd "$(dirname "$0")/.."

echo "========================================================================"
echo "  PDSS Uninstaller"
echo "========================================================================"
echo ""
echo "WARNING: This will remove all PDSS containers and data!"
echo ""
read -p "Are you sure? Type 'YES' to confirm: " CONFIRM

if [ "$CONFIRM" != "YES" ]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo ""
echo "Stopping and removing containers..."
docker-compose down -v

echo ""
echo "PDSS has been uninstalled."
echo ""
'@
$uninstallScript -replace "`r`n", "`n" | Out-File -FilePath "$OUTPUT_DIR\scripts\uninstall.sh" -Encoding UTF8 -NoNewline

Write-ColorOutput Green "[OK] Management scripts created"
Write-Host ""

Write-Host "[3/5] Creating systemd service file..."
@"
[Unit]
Description=Procurement Decision Support System (PDSS)
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/pdss
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
"@ | Out-File -FilePath "$OUTPUT_DIR\systemd\pdss.service" -Encoding UTF8
Write-ColorOutput Green "[OK] Systemd service file created"
Write-Host ""

Write-Host "[4/5] Creating verification script..."
$verifyScript = @'
#!/bin/bash

echo "========================================================================"
echo "  PDSS Package Verification"
echo "========================================================================"
echo ""
echo "Checking package integrity..."
echo ""

ERRORS=0

echo "[1] Checking critical files:"
files=(
    "docker-compose.yml"
    "backend/Dockerfile"
    "frontend/Dockerfile"
    "backend/requirements.txt"
    "frontend/package.json"
    "install.sh"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file - MISSING!"
        ((ERRORS++))
    fi
done
echo ""

echo "[2] Checking Docker Compose configuration:"
if grep -q "postgres:" docker-compose.yml 2>/dev/null; then
    echo "  ✅ PostgreSQL service configured"
else
    echo "  ❌ PostgreSQL service missing"
    ((ERRORS++))
fi

if grep -q "backend:" docker-compose.yml 2>/dev/null; then
    echo "  ✅ Backend service configured"
else
    echo "  ❌ Backend service missing"
    ((ERRORS++))
fi

if grep -q "frontend:" docker-compose.yml 2>/dev/null; then
    echo "  ✅ Frontend service configured"
else
    echo "  ❌ Frontend service missing"
    ((ERRORS++))
fi
echo ""

if [ $ERRORS -eq 0 ]; then
    echo "========================================================================"
    echo "  VERIFICATION PASSED - Package is ready for deployment!"
    echo "========================================================================"
    exit 0
else
    echo "========================================================================"
    echo "  VERIFICATION FAILED - $ERRORS error(s) found!"
    echo "========================================================================"
    exit 1
fi
'@
$verifyScript -replace "`r`n", "`n" | Out-File -FilePath "$OUTPUT_DIR\verify_package.sh" -Encoding UTF8 -NoNewline
Write-ColorOutput Green "[OK] Verification script created (Unix line endings)"
Write-Host ""

Write-Host "[5/5] Creating README..."
@"
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

INSTALLATION INSTRUCTIONS:
  1. Ensure Docker and Docker Compose are installed
  2. Run: chmod +x install.sh
  3. Run: sudo ./install.sh
  4. Follow the on-screen instructions
  5. Access the system at http://localhost:3000

MANAGEMENT SCRIPTS (in scripts folder):
  - start.sh          Start the PDSS system
  - stop.sh           Stop the PDSS system
  - restart.sh        Restart the PDSS system
  - status.sh         Check system status
  - logs.sh           View system logs
  - backup.sh         Backup database
  - uninstall.sh      Uninstall PDSS

DEFAULT CREDENTIALS:
  Admin:       admin / admin123
  Finance:     finance1 / finance123
  PM:          pm1 / pm123
  Procurement: proc1 / proc123

  IMPORTANT: Change passwords after first login!

DOCUMENTATION:
  See the 'docs' folder for complete documentation

========================================================================
  Created: $TIMESTAMP_FRIENDLY
  Package: $OUTPUT_DIR
========================================================================
"@ | Out-File -FilePath "$OUTPUT_DIR\README.txt" -Encoding UTF8
Write-ColorOutput Green "[OK] README created"
Write-Host ""

################################################################################
# PACKAGE FINALIZATION
################################################################################

Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "  PACKAGE FINALIZATION" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "[1/2] Calculating package size..."
$SIZE = (Get-ChildItem -Path $OUTPUT_DIR -Recurse | Measure-Object -Property Length -Sum).Sum
$SIZE_MB = [math]::Round($SIZE / 1MB, 2)
Write-ColorOutput Green "[OK] Package size: $SIZE_MB MB"
Write-Host ""

Write-Host "[2/2] Creating package manifest..."
@"
PDSS Linux Installation Package
========================================================================
Version: $VERSION
Build: $TIMESTAMP
Created: $TIMESTAMP_FRIENDLY
Platform: Linux
Size: $SIZE_MB MB

Package Contents:
├── install.sh                Main installer
├── README.txt                Package information
├── verify_package.sh         Package verification
├── PACKAGE_INFO.txt          Detailed package info
├── version.json              Version metadata
├── docker-compose.yml        Docker orchestration
├── backend/                  Backend application
├── frontend/                 Frontend application
├── docs/                     Documentation
├── scripts/                  Management scripts
├── config/                   Configuration templates
└── systemd/                  Systemd service file

Installation:
  1. Run chmod +x install.sh && ./verify_package.sh
  2. Run sudo ./install.sh
  3. Access at http://localhost:3000

"@ | Out-File -FilePath "$OUTPUT_DIR\MANIFEST.txt" -Encoding UTF8
Write-ColorOutput Green "[OK] Manifest created"
Write-Host ""

################################################################################
# CREATING ARCHIVE
################################################################################

Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "  CREATING ARCHIVE" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "[1/1] Creating ZIP archive..."
Compress-Archive -Path "$OUTPUT_DIR\*" -DestinationPath $ZIP_NAME -Force
$ZIP_SIZE = [math]::Round((Get-Item $ZIP_NAME).Length / 1MB, 2)
Write-ColorOutput Green "[OK] ZIP archive created: $ZIP_NAME ($ZIP_SIZE MB)"
Write-Host ""

################################################################################
# BUILD COMPLETE
################################################################################

Write-Host "============================================================================" -ForegroundColor Green
Write-Host "  BUILD COMPLETE!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Package Details:" -ForegroundColor Cyan
Write-Host "  Name:     $OUTPUT_DIR"
Write-Host "  Version:  $VERSION"
Write-Host "  Build:    $TIMESTAMP"
Write-Host "  Size:     $SIZE_MB MB"
Write-Host "  Archive:  $ZIP_NAME ($ZIP_SIZE MB)"
Write-Host ""
Write-Host "Package Location:" -ForegroundColor Cyan
Write-Host "  Folder:   $(Get-Location)\$OUTPUT_DIR"
Write-Host "  ZIP:      $(Get-Location)\$ZIP_NAME"
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Transfer to Linux system"
Write-Host "  2. Extract: unzip $ZIP_NAME"
Write-Host "  3. Navigate: cd $OUTPUT_DIR"
Write-Host "  4. Run: chmod +x install.sh && sudo ./install.sh"
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""

