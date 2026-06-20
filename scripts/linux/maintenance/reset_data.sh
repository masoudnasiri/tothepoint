#!/bin/bash

echo "============================================================================"
echo "PDSS DATA RESET AND RESEED"
echo "============================================================================"
echo ""
echo "This will wipe all operational data and create fresh test data with:"
echo "  - USD and Iranian Rial (IRR) currencies"
echo "  - Realistic IT equipment projects"
echo "  - Mixed USD/IRR pricing for procurement options"
echo ""
echo "WARNING: This will delete all existing data except the admin user!"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

echo ""
echo "Running reset script..."
echo ""

python3 backend/reset_and_reseed_data.py

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================================"
    echo "SUCCESS! Data has been reset and reseeded."
    echo "============================================================================"
    echo ""
    echo "Next step: Restart the backend"
    echo "  docker-compose restart backend"
    echo ""
else
    echo ""
    echo "============================================================================"
    echo "ERROR! Something went wrong."
    echo "============================================================================"
    echo ""
    echo "Please check the error message above."
    echo ""
fi

