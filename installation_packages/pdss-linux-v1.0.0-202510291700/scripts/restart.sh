#!/bin/bash
cd "$(dirname "$0")/.."
echo "Restarting PDSS..."
docker-compose restart
echo "PDSS restarted successfully!"