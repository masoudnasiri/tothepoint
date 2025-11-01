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