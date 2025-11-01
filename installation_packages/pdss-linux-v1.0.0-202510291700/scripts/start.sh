#!/bin/bash
cd "$(dirname "$0")/.."
docker-compose up -d
sleep 5
echo "PDSS started successfully!"
xdg-open http://localhost:3000 2>/dev/null || echo "Access at: http://localhost:3000"