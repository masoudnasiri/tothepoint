#!/bin/bash
# Quick fix script for existing Linux installation packages
# Run this in your installation directory

set -e

echo "============================================================================"
echo "  PDSS Installation - Quick Fix Script"
echo "============================================================================"
echo ""

echo "[1/4] Fixing script line endings..."
sed -i 's/\r$//' install.sh
chmod +x install.sh
chmod +x scripts/*.sh 2>/dev/null || true
echo "[OK] Line endings fixed"
echo ""

echo "[2/4] Verifying Docker..."
if ! command -v docker >/dev/null 2>&1; then
    echo "[ERROR] Docker not found!"
    exit 1
fi
echo "[OK] Docker found: $(docker --version)"
echo ""

echo "[3/4] Pre-pulling base images..."
echo "This may take a few minutes..."
if docker pull python:3.11-slim; then
    echo "[OK] Python base image ready"
else
    echo "[WARNING] Failed to pull python:3.11-slim - may need network/firewall configuration"
fi

if docker pull node:18-alpine; then
    echo "[OK] Node base image ready"
else
    echo "[WARNING] Failed to pull node:18-alpine - may need network/firewall configuration"
fi

if docker pull postgres:15-alpine; then
    echo "[OK] PostgreSQL base image ready"
else
    echo "[WARNING] Failed to pull postgres:15-alpine - may need network/firewall configuration"
fi
echo ""

echo "[4/4] Verifying files..."
if [ ! -f "backend/Dockerfile" ]; then
    echo "[ERROR] Backend Dockerfile not found!"
    exit 1
fi
if [ ! -f "frontend/Dockerfile" ]; then
    echo "[ERROR] Frontend Dockerfile not found!"
    exit 1
fi
if [ ! -f "docker-compose.yml" ]; then
    echo "[ERROR] docker-compose.yml not found!"
    exit 1
fi
echo "[OK] All required files found"
echo ""

echo "============================================================================"
echo "  Ready to install! Run: sudo ./install.sh"
echo "============================================================================"
echo ""

