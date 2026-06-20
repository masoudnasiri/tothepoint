#!/bin/bash

# Procurement DSS Stop Script

echo "Stopping Procurement DSS System..."

# Stop and remove containers
docker-compose down

# Remove volumes (uncomment the next line if you want to remove all data)
# docker-compose down -v

echo "Procurement DSS system stopped."
