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