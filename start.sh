#!/bin/bash

# Procurement DSS Startup Script

echo "Starting Procurement DSS System..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed. Please install docker-compose and try again."
    exit 1
fi

# Stop any existing containers
echo "Stopping existing containers..."
docker-compose down

# Build and start services
echo "Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "Checking service status..."
docker-compose ps

echo ""
echo "🎉 Procurement DSS is now running!"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "Default Login Credentials:"
echo "  Admin: admin / admin123"
echo "  PM: pm1 / pm123"
echo "  Procurement: proc1 / proc123"
echo "  Finance: finance1 / finance123"
echo ""
echo "To stop the system, run: docker-compose down"
echo "To view logs, run: docker-compose logs -f"
