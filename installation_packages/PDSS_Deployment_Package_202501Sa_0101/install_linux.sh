#!/bin/bash
################################################################################
#  Procurement Decision Support System - Linux Installer
#  One-Click Installation for Linux (Ubuntu/Debian/CentOS/RHEL)
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "========================================================================"
echo "  PROCUREMENT DECISION SUPPORT SYSTEM"
echo "  Linux Installation Wizard"
echo "========================================================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${YELLOW}[WARNING] Running as root. It's recommended to run as regular user.${NC}"
    echo ""
fi

echo "[1/9] Checking prerequisites..."
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR] Docker is not installed!${NC}"
    echo ""
    echo "Please install Docker first:"
    echo ""
    echo "For Ubuntu/Debian:"
    echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "  sudo sh get-docker.sh"
    echo "  sudo usermod -aG docker \$USER"
    echo "  newgrp docker"
    echo ""
    echo "For CentOS/RHEL:"
    echo "  sudo yum install -y docker"
    echo "  sudo systemctl start docker"
    echo "  sudo systemctl enable docker"
    echo "  sudo usermod -aG docker \$USER"
    echo ""
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Docker found: $(docker --version)"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}[ERROR] Docker Compose is not installed!${NC}"
    echo ""
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}[OK]${NC} Docker Compose installed"
fi
echo -e "${GREEN}[OK]${NC} Docker Compose found: $(docker-compose --version)"

# Check if Docker daemon is running
if ! docker ps &> /dev/null; then
    echo -e "${RED}[ERROR] Docker daemon is not running!${NC}"
    echo ""
    echo "Starting Docker..."
    sudo systemctl start docker
    sleep 5
    
    if ! docker ps &> /dev/null; then
        echo -e "${RED}[ERROR] Failed to start Docker!${NC}"
        echo "Please start Docker manually: sudo systemctl start docker"
        exit 1
    fi
fi
echo -e "${GREEN}[OK]${NC} Docker daemon is running"
echo ""

echo "[2/9] Stopping any existing containers..."
docker-compose down &> /dev/null || true
echo -e "${GREEN}[OK]${NC} Cleanup complete"
echo ""

echo "[3/9] Building Docker images..."
echo "This may take 5-10 minutes on first installation..."
if ! docker-compose build; then
    echo -e "${RED}[ERROR] Failed to build Docker images!${NC}"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Images built successfully"
echo ""

echo "[4/9] Starting database..."
if ! docker-compose up -d db; then
    echo -e "${RED}[ERROR] Failed to start database!${NC}"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Database started"
echo "Waiting for database to be ready..."
sleep 10
echo ""

echo "[5/9] Starting backend service..."
if ! docker-compose up -d backend; then
    echo -e "${RED}[ERROR] Failed to start backend!${NC}"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Backend started"
echo "Waiting for backend to be ready..."
sleep 15
echo ""

echo "[6/9] Starting frontend service..."
if ! docker-compose up -d frontend; then
    echo -e "${RED}[ERROR] Failed to start frontend!${NC}"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Frontend started"
echo "Waiting for frontend to be ready..."
sleep 20
echo ""

echo "[7/9] Verifying installation..."
docker-compose ps
echo ""

echo "[8/9] Creating management scripts..."
INSTALL_DIR="$(pwd)"

# Create start script
cat > "$HOME/start-pdss.sh" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
docker-compose up -d
sleep 5
echo "Platform started! Opening browser..."
xdg-open http://localhost:3000 2>/dev/null || sensible-browser http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000 in your browser"
EOF
chmod +x "$HOME/start-pdss.sh"

# Create stop script
cat > "$HOME/stop-pdss.sh" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
docker-compose down
echo "Platform stopped!"
EOF
chmod +x "$HOME/stop-pdss.sh"

# Create logs script
cat > "$HOME/logs-pdss.sh" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
docker-compose logs -f
EOF
chmod +x "$HOME/logs-pdss.sh"

echo -e "${GREEN}[OK]${NC} Management scripts created in $HOME"
echo ""

echo "[9/9] Creating desktop shortcuts (if desktop environment detected)..."
if [ -d "$HOME/Desktop" ]; then
    # Create .desktop files for Linux desktop environments
    cat > "$HOME/Desktop/start-pdss.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Start PDSS
Comment=Start Procurement Decision Support System
Exec=$HOME/start-pdss.sh
Icon=applications-internet
Terminal=true
Categories=Application;
EOF
    chmod +x "$HOME/Desktop/start-pdss.desktop"
    
    cat > "$HOME/Desktop/stop-pdss.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Stop PDSS
Comment=Stop Procurement Decision Support System
Exec=$HOME/stop-pdss.sh
Icon=applications-internet
Terminal=true
Categories=Application;
EOF
    chmod +x "$HOME/Desktop/stop-pdss.desktop"
    
    echo -e "${GREEN}[OK]${NC} Desktop shortcuts created"
else
    echo -e "${YELLOW}[SKIP]${NC} No desktop environment detected"
fi
echo ""

echo "========================================================================"
echo "  INSTALLATION COMPLETE!"
echo "========================================================================"
echo ""
echo "The platform is now running at: http://localhost:3000"
echo ""
echo "Default Login Credentials:"
echo "  Admin:       Username: admin      Password: admin123"
echo "  Finance:     Username: finance1   Password: finance123"
echo "  PM:          Username: pm1        Password: pm123"
echo "  Procurement: Username: proc1      Password: proc123"
echo ""
echo "Management Scripts Created:"
echo "  $HOME/start-pdss.sh  - Start the platform"
echo "  $HOME/stop-pdss.sh   - Stop the platform"
echo "  $HOME/logs-pdss.sh   - View logs"
echo ""
echo "Opening browser in 5 seconds..."
sleep 5
xdg-open http://localhost:3000 2>/dev/null || sensible-browser http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000 in your browser"
echo ""
echo "========================================================================"
echo "Press any key to exit..."
read -n 1 -s

