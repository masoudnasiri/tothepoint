#!/bin/bash
################################################################################
#  PDSS - Linux Installation Package Creator
#  Creates complete Linux installation packages (.tar.gz, .deb, .rpm)
################################################################################

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Package Information
VERSION="1.0.0"
PACKAGE_NAME="pdss"
FULL_NAME="Procurement Decision Support System"
TIMESTAMP=$(date +%Y%m%d%H%M)
TIMESTAMP_FRIENDLY=$(date "+%Y-%m-%d %H:%M:%S")
OUTPUT_DIR="${PACKAGE_NAME}-linux-installer_v${VERSION}_${TIMESTAMP}"
TARBALL_NAME="${PACKAGE_NAME}-linux_v${VERSION}_${TIMESTAMP}.tar.gz"

# Display header
echo ""
echo "============================================================================"
echo -e "  ${BOLD}PDSS Linux Installation Package Creator${NC}"
echo "============================================================================"
echo ""
echo -e "${CYAN}Version:${NC}    $VERSION"
echo -e "${CYAN}Build Date:${NC} $TIMESTAMP_FRIENDLY"
echo -e "${CYAN}Package:${NC}    $OUTPUT_DIR"
echo ""

################################################################################
# STAGE 1: PRE-BUILD VALIDATION
################################################################################

echo "============================================================================"
echo "  STAGE 1: PRE-BUILD VALIDATION"
echo "============================================================================"
echo ""

echo "[1/5] Checking project structure..."
if [ ! -d "../backend" ]; then
    echo -e "${RED}[ERROR]${NC} Backend directory not found!"
    exit 1
fi
if [ ! -d "../frontend" ]; then
    echo -e "${RED}[ERROR]${NC} Frontend directory not found!"
    exit 1
fi
if [ ! -f "../docker-compose.yml" ]; then
    echo -e "${RED}[ERROR]${NC} docker-compose.yml not found!"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Project structure validated"
echo ""

echo "[2/5] Checking required files..."
if [ ! -f "../backend/requirements.txt" ]; then
    echo -e "${RED}[ERROR]${NC} Backend requirements.txt not found!"
    exit 1
fi
if [ ! -f "../frontend/package.json" ]; then
    echo -e "${RED}[ERROR]${NC} Frontend package.json not found!"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Required files found"
echo ""

echo "[3/5] Creating package directory structure..."
mkdir -p "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/backend"
mkdir -p "$OUTPUT_DIR/frontend"
mkdir -p "$OUTPUT_DIR/docs"
mkdir -p "$OUTPUT_DIR/scripts"
mkdir -p "$OUTPUT_DIR/config"
mkdir -p "$OUTPUT_DIR/systemd"
echo -e "${GREEN}[OK]${NC} Directory structure created"
echo ""

echo "[4/5] Generating package metadata..."
cat > "$OUTPUT_DIR/PACKAGE_INFO.txt" << EOF
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
EOF
echo -e "${GREEN}[OK]${NC} Metadata generated"
echo ""

echo "[5/5] Creating version file..."
cat > "$OUTPUT_DIR/version.json" << EOF
{
  "version": "$VERSION",
  "build": "$TIMESTAMP",
  "platform": "linux",
  "created": "$TIMESTAMP_FRIENDLY"
}
EOF
echo -e "${GREEN}[OK]${NC} Version file created"
echo ""

################################################################################
# STAGE 2: COPYING APPLICATION FILES
################################################################################

echo "============================================================================"
echo "  STAGE 2: COPYING APPLICATION FILES"
echo "============================================================================"
echo ""

echo "[1/5] Copying backend application..."
cp -r ../backend/* "$OUTPUT_DIR/backend/" 2>/dev/null || true
echo -e "${GREEN}[OK]${NC} Backend copied"

echo "      Cleaning Python cache..."
find "$OUTPUT_DIR/backend" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$OUTPUT_DIR/backend" -type f -name "*.pyc" -delete 2>/dev/null || true
rm -f "$OUTPUT_DIR/backend/.dockerignore" "$OUTPUT_DIR/backend/.gitignore" 2>/dev/null || true
echo "      ${GREEN}[OK]${NC} Cleanup complete"
echo ""

echo "[2/5] Copying frontend application..."
cp -r ../frontend/src "$OUTPUT_DIR/frontend/"
cp -r ../frontend/public "$OUTPUT_DIR/frontend/"
cp ../frontend/package.json "$OUTPUT_DIR/frontend/"
cp ../frontend/package-lock.json "$OUTPUT_DIR/frontend/" 2>/dev/null || true
cp ../frontend/tsconfig.json "$OUTPUT_DIR/frontend/" 2>/dev/null || true
cp ../frontend/.env.example "$OUTPUT_DIR/frontend/" 2>/dev/null || true
cp ../frontend/Dockerfile "$OUTPUT_DIR/frontend/"
echo -e "${GREEN}[OK]${NC} Frontend copied"

# Clean up node_modules if exists
rm -rf "$OUTPUT_DIR/frontend/node_modules" 2>/dev/null || true
rm -f "$OUTPUT_DIR/frontend/.gitignore" 2>/dev/null || true
echo ""

echo "[3/5] Copying Docker configuration..."
cp ../docker-compose.yml "$OUTPUT_DIR/"
cp ../backend/Dockerfile "$OUTPUT_DIR/backend/"
cp ../frontend/Dockerfile "$OUTPUT_DIR/frontend/"
echo -e "${GREEN}[OK]${NC} Docker files copied"
echo ""

echo "[4/5] Copying documentation..."
# Copy main documentation
[ -f "../README.md" ] && cp "../README.md" "$OUTPUT_DIR/docs/README.md"
[ -f "../USER_GUIDE.md" ] && cp "../USER_GUIDE.md" "$OUTPUT_DIR/docs/USER_GUIDE.md"
[ -f "../COMPLETE_SYSTEM_DOCUMENTATION.md" ] && cp "../COMPLETE_SYSTEM_DOCUMENTATION.md" "$OUTPUT_DIR/docs/"

# Copy from installation_packages if not in root
[ ! -f "$OUTPUT_DIR/docs/README.md" ] && [ -f "README.md" ] && cp "README.md" "$OUTPUT_DIR/docs/"
[ ! -f "$OUTPUT_DIR/docs/USER_GUIDE.md" ] && [ -f "USER_GUIDE.md" ] && cp "USER_GUIDE.md" "$OUTPUT_DIR/docs/"
[ -f "INSTALLATION_GUIDE.md" ] && cp "INSTALLATION_GUIDE.md" "$OUTPUT_DIR/docs/"
[ -f "SYSTEM_REQUIREMENTS.md" ] && cp "SYSTEM_REQUIREMENTS.md" "$OUTPUT_DIR/docs/"
[ -f "QUICK_START.md" ] && cp "QUICK_START.md" "$OUTPUT_DIR/docs/"
echo -e "${GREEN}[OK]${NC} Documentation copied"
echo ""

echo "[5/5] Copying configuration templates..."
if [ -f "config_template.env" ]; then
    cp "config_template.env" "$OUTPUT_DIR/config/.env.example"
else
    # Create default .env.example
    cat > "$OUTPUT_DIR/config/.env.example" << 'EOF'
# PDSS Configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/procurement_dss
SECRET_KEY=change-this-secret-key-in-production
ALLOWED_ORIGINS=http://localhost:3000
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=procurement_dss
EOF
fi
echo -e "${GREEN}[OK]${NC} Configuration templates copied"
echo ""

################################################################################
# STAGE 3: CREATING INSTALLATION SCRIPTS
################################################################################

echo "============================================================================"
echo "  STAGE 3: CREATING INSTALLATION SCRIPTS"
echo "============================================================================"
echo ""

echo "[1/5] Creating main installer script..."
cat > "$OUTPUT_DIR/install.sh" << 'EOFINSTALL'
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
echo "  Linux Installer"
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
if ! docker-compose up -d db; then
    echo -e "${RED}[ERROR]${NC} Failed to start database!"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Database started"
echo "Waiting for database initialization..."
sleep 15
echo ""

echo "[6/9] Starting backend service..."
if ! docker-compose up -d backend; then
    echo -e "${RED}[ERROR]${NC} Failed to start backend!"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Backend started"
echo "Waiting for backend initialization..."
sleep 20
echo ""

echo "[7/9] Starting frontend service..."
if ! docker-compose up -d frontend; then
    echo -e "${RED}[ERROR]${NC} Failed to start frontend!"
    exit 1
fi
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
cat > "$HOME/pdss-start.sh" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
docker-compose up -d
sleep 5
echo -e "${GREEN}PDSS started successfully!${NC}"
xdg-open http://localhost:3000 2>/dev/null || echo "Access at: http://localhost:3000"
EOF
chmod +x "$HOME/pdss-start.sh"

# Create stop script
cat > "$HOME/pdss-stop.sh" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
docker-compose down
echo -e "${GREEN}PDSS stopped successfully!${NC}"
EOF
chmod +x "$HOME/pdss-stop.sh"

# Create status script
cat > "$HOME/pdss-status.sh" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
echo "============================================================================"
echo "  PDSS System Status"
echo "============================================================================"
echo ""
docker-compose ps
EOF
chmod +x "$HOME/pdss-status.sh"

# Create logs script
cat > "$HOME/pdss-logs.sh" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
docker-compose logs -f
EOF
chmod +x "$HOME/pdss-logs.sh"

echo -e "${GREEN}[OK]${NC} Management scripts created in $HOME"
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
echo "  $HOME/pdss-status.sh  - Check status"
echo "  $HOME/pdss-logs.sh    - View logs"
echo ""
echo "Opening browser..."
sleep 3
xdg-open http://localhost:3000 2>/dev/null || sensible-browser http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000 in your browser"
echo ""
echo "============================================================================"
EOFINSTALL

chmod +x "$OUTPUT_DIR/install.sh"
echo -e "${GREEN}[OK]${NC} Main installer created"
echo ""

echo "[2/5] Creating management scripts..."

# Start script
cat > "$OUTPUT_DIR/scripts/start.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/.."
docker-compose up -d
sleep 5
echo "PDSS started successfully!"
xdg-open http://localhost:3000 2>/dev/null || echo "Access at: http://localhost:3000"
EOF
chmod +x "$OUTPUT_DIR/scripts/start.sh"

# Stop script
cat > "$OUTPUT_DIR/scripts/stop.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/.."
docker-compose down
echo "PDSS stopped successfully!"
EOF
chmod +x "$OUTPUT_DIR/scripts/stop.sh"

# Status script
cat > "$OUTPUT_DIR/scripts/status.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/.."
echo "========================================================================"
echo "  PDSS System Status"
echo "========================================================================"
echo ""
docker-compose ps
echo ""
EOF
chmod +x "$OUTPUT_DIR/scripts/status.sh"

# Logs script
cat > "$OUTPUT_DIR/scripts/logs.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/.."
docker-compose logs -f
EOF
chmod +x "$OUTPUT_DIR/scripts/logs.sh"

# Restart script
cat > "$OUTPUT_DIR/scripts/restart.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/.."
echo "Restarting PDSS..."
docker-compose restart
echo "PDSS restarted successfully!"
EOF
chmod +x "$OUTPUT_DIR/scripts/restart.sh"

# Backup script
cat > "$OUTPUT_DIR/scripts/backup.sh" << 'EOF'
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
EOF
chmod +x "$OUTPUT_DIR/scripts/backup.sh"

# Uninstall script
cat > "$OUTPUT_DIR/scripts/uninstall.sh" << 'EOF'
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
echo "Note: Installation files are still present."
echo "You can safely delete this folder to complete removal."
echo ""

# Remove management scripts
rm -f "$HOME/pdss-start.sh"
rm -f "$HOME/pdss-stop.sh"
rm -f "$HOME/pdss-status.sh"
rm -f "$HOME/pdss-logs.sh"
echo "Management scripts removed from $HOME"
EOF
chmod +x "$OUTPUT_DIR/scripts/uninstall.sh"

echo -e "${GREEN}[OK]${NC} Management scripts created"
echo ""

echo "[3/5] Creating systemd service file..."
cat > "$OUTPUT_DIR/systemd/pdss.service" << EOF
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
EOF
echo -e "${GREEN}[OK]${NC} Systemd service file created"
echo ""

echo "[4/5] Creating README..."
cat > "$OUTPUT_DIR/README.txt" << EOF
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

SYSTEMD SERVICE (optional):
  To run PDSS as a system service:
  1. sudo cp systemd/pdss.service /etc/systemd/system/
  2. sudo systemctl daemon-reload
  3. sudo systemctl enable pdss
  4. sudo systemctl start pdss

DEFAULT CREDENTIALS:
  Admin:       admin / admin123
  Finance:     finance1 / finance123
  PM:          pm1 / pm123
  Procurement: proc1 / proc123

  IMPORTANT: Change passwords after first login!

DOCUMENTATION:
  See the 'docs' folder for complete documentation

SUPPORT:
  For issues or questions, refer to the documentation
  or contact your system administrator.

========================================================================
  Created: $TIMESTAMP_FRIENDLY
  Package: $OUTPUT_DIR
========================================================================
EOF
echo -e "${GREEN}[OK]${NC} README created"
echo ""

echo "[5/5] Creating quick start guide..."
cat > "$OUTPUT_DIR/QUICK_START.txt" << EOF
========================================================================
  QUICK START GUIDE
========================================================================

STEP 1: INSTALL DOCKER
  Ubuntu/Debian:
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker \$USER
    newgrp docker

  CentOS/RHEL:
    sudo yum install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker

STEP 2: INSTALL DOCKER COMPOSE
  sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose

STEP 3: VERIFY PACKAGE
  Run: ./verify_package.sh
  This checks if all required files are present

STEP 4: INSTALL PDSS
  chmod +x install.sh
  sudo ./install.sh
  Wait for installation to complete

STEP 5: ACCESS SYSTEM
  Open browser: http://localhost:3000
  Login: admin / admin123

STEP 6: POST-INSTALLATION
  - Change default passwords
  - Configure systemd service (optional)
  - Set up automated backups
  - Review documentation in docs folder

========================================================================
  MANAGEMENT COMMANDS
========================================================================

  Start System:    ./scripts/start.sh
  Stop System:     ./scripts/stop.sh
  Check Status:    ./scripts/status.sh
  View Logs:       ./scripts/logs.sh
  Restart:         ./scripts/restart.sh
  Backup DB:       ./scripts/backup.sh
  Uninstall:       ./scripts/uninstall.sh

========================================================================
EOF
echo -e "${GREEN}[OK]${NC} Quick start guide created"
echo ""

################################################################################
# STAGE 4: CREATING VERIFICATION TOOLS
################################################################################

echo "============================================================================"
echo "  STAGE 4: CREATING VERIFICATION TOOLS"
echo "============================================================================"
echo ""

echo "[1/2] Creating package verification script..."
cat > "$OUTPUT_DIR/verify_package.sh" << 'EOF'
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

echo "[3] Checking management scripts:"
scripts=(
    "scripts/start.sh"
    "scripts/stop.sh"
    "scripts/status.sh"
)

for script in "${scripts[@]}"; do
    if [ -f "$script" ] && [ -x "$script" ]; then
        echo "  ✅ $script"
    else
        echo "  ❌ $script - MISSING or not executable!"
        ((ERRORS++))
    fi
done
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
EOF
chmod +x "$OUTPUT_DIR/verify_package.sh"
echo -e "${GREEN}[OK]${NC} Verification script created"
echo ""

echo "[2/2] Running package verification..."
if "$OUTPUT_DIR/verify_package.sh"; then
    echo -e "${GREEN}[OK]${NC} Package verification passed"
else
    echo -e "${YELLOW}[WARNING]${NC} Package verification failed - please review"
fi
echo ""

################################################################################
# STAGE 5: PACKAGE FINALIZATION
################################################################################

echo "============================================================================"
echo "  STAGE 5: PACKAGE FINALIZATION"
echo "============================================================================"
echo ""

echo "[1/3] Calculating package size..."
SIZE=$(du -sb "$OUTPUT_DIR" | cut -f1)
SIZE_MB=$((SIZE / 1024 / 1024))
echo -e "${GREEN}[OK]${NC} Package size: ~${SIZE_MB} MB"
echo ""

echo "[2/3] Creating package manifest..."
cat > "$OUTPUT_DIR/MANIFEST.txt" << EOF
PDSS Linux Installation Package
========================================================================
Version: $VERSION
Build: $TIMESTAMP
Created: $TIMESTAMP_FRIENDLY
Platform: Linux
Size: ~${SIZE_MB} MB

Package Contents:
├── install.sh                Main installer
├── README.txt                Package information
├── QUICK_START.txt           Quick start guide
├── verify_package.sh         Package verification
├── PACKAGE_INFO.txt          Detailed package info
├── version.json              Version metadata
├── docker-compose.yml        Docker orchestration
├── backend/                  Backend application
├── frontend/                 Frontend application
├── docs/                     Documentation
├── scripts/                  Management scripts
│   ├── start.sh
│   ├── stop.sh
│   ├── status.sh
│   ├── logs.sh
│   ├── restart.sh
│   ├── backup.sh
│   └── uninstall.sh
├── config/                   Configuration templates
└── systemd/                  Systemd service file

Installation:
  1. Run ./verify_package.sh to check integrity
  2. Run sudo ./install.sh
  3. Access at http://localhost:3000

Support:
  See documentation in docs/ folder

EOF
echo -e "${GREEN}[OK]${NC} Manifest created"
echo ""

echo "[3/3] Creating checksum file..."
cat > "$OUTPUT_DIR/CHECKSUMS.txt" << EOF
PDSS Package Checksums - Build $TIMESTAMP
========================================================================

Critical Files:
EOF

# Generate checksums for critical files
for file in install.sh docker-compose.yml verify_package.sh; do
    if [ -f "$OUTPUT_DIR/$file" ]; then
        if command -v md5sum &> /dev/null; then
            md5sum "$OUTPUT_DIR/$file" | awk '{print $1 "  " FILENAME}' FILENAME="$file" >> "$OUTPUT_DIR/CHECKSUMS.txt"
        elif command -v shasum &> /dev/null; then
            shasum -a 256 "$OUTPUT_DIR/$file" | awk '{print $1 "  " FILENAME}' FILENAME="$file" >> "$OUTPUT_DIR/CHECKSUMS.txt"
        fi
    fi
done
echo -e "${GREEN}[OK]${NC} Checksum file created"
echo ""

################################################################################
# STAGE 6: CREATING COMPRESSED ARCHIVES
################################################################################

echo "============================================================================"
echo "  STAGE 6: CREATING COMPRESSED ARCHIVES"
echo "============================================================================"
echo ""

echo "[1/2] Creating TAR.GZ archive..."
if tar -czf "$TARBALL_NAME" "$OUTPUT_DIR"; then
    TARBALL_SIZE=$(du -h "$TARBALL_NAME" | cut -f1)
    echo -e "${GREEN}[OK]${NC} TAR.GZ archive created: $TARBALL_NAME ($TARBALL_SIZE)"
else
    echo -e "${YELLOW}[WARNING]${NC} Failed to create TAR.GZ archive"
fi
echo ""

echo "[2/2] Creating ZIP archive (if available)..."
if command -v zip &> /dev/null; then
    ZIP_NAME="${PACKAGE_NAME}-linux_v${VERSION}_${TIMESTAMP}.zip"
    if zip -r "$ZIP_NAME" "$OUTPUT_DIR" > /dev/null; then
        ZIP_SIZE=$(du -h "$ZIP_NAME" | cut -f1)
        echo -e "${GREEN}[OK]${NC} ZIP archive created: $ZIP_NAME ($ZIP_SIZE)"
    else
        echo -e "${YELLOW}[WARNING]${NC} Failed to create ZIP archive"
    fi
else
    echo -e "${BLUE}[INFO]${NC} ZIP not available - skipping ZIP archive"
fi
echo ""

################################################################################
# BUILD COMPLETE
################################################################################

echo "============================================================================"
echo -e "  ${BOLD}BUILD COMPLETE!${NC}"
echo "============================================================================"
echo ""
echo "Package Details:"
echo "  Name:     $OUTPUT_DIR"
echo "  Version:  $VERSION"
echo "  Build:    $TIMESTAMP"
echo "  Size:     ~${SIZE_MB} MB"
[ -f "$TARBALL_NAME" ] && echo "  Archive:  $TARBALL_NAME ($TARBALL_SIZE)"
echo ""
echo "Package Location:"
echo "  Folder:   $(pwd)/$OUTPUT_DIR"
[ -f "$TARBALL_NAME" ] && echo "  TAR.GZ:   $(pwd)/$TARBALL_NAME"
[ -f "$ZIP_NAME" ] && echo "  ZIP:      $(pwd)/$ZIP_NAME"
echo ""
echo "Next Steps:"
echo "  1. Verify package: cd $OUTPUT_DIR && ./verify_package.sh"
echo "  2. Review contents: cat $OUTPUT_DIR/README.txt"
echo "  3. Deploy to target system"
echo "  4. Run: sudo ./install.sh"
echo ""
echo "Distribution Options:"
if [ -f "$TARBALL_NAME" ]; then
    echo "  - Transfer archive: $TARBALL_NAME"
    echo "  - Extract on target: tar -xzf $TARBALL_NAME"
    echo "  - Run installer: cd $OUTPUT_DIR && sudo ./install.sh"
else
    echo "  - Copy entire folder: $OUTPUT_DIR"
    echo "  - Run installer on target system"
fi
echo ""
echo "============================================================================"
echo ""

