#!/bin/bash

# OR-Tools Enhancement Installation Script
# This script installs the enhanced OR-Tools optimization features

echo "=================================="
echo "OR-Tools Enhancement Installation"
echo "=================================="
echo ""

# Step 1: Check if in correct directory
if [ ! -f "backend/requirements.txt" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

echo "✅ Project root directory detected"
echo ""

# Step 2: Install Python dependencies
echo "📦 Installing Python dependencies..."
cd backend

# Check if venv exists
if [ -d "venv" ]; then
    echo "🐍 Virtual environment detected"
    source venv/bin/activate
fi

# Install networkx
pip install networkx==3.2.1

if [ $? -eq 0 ]; then
    echo "✅ networkx installed successfully"
else
    echo "❌ Failed to install networkx"
    exit 1
fi

cd ..
echo ""

# Step 3: Verify installation
echo "🔍 Verifying installation..."

python3 -c "import networkx; print('✅ NetworkX version:', networkx.__version__)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Could not verify networkx installation"
else
    echo "✅ NetworkX verified"
fi

python3 -c "import ortools; print('✅ OR-Tools version:', ortools.__version__)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Could not verify OR-Tools installation"
else
    echo "✅ OR-Tools verified"
fi

echo ""

# Step 4: Summary
echo "=================================="
echo "✅ Installation Complete!"
echo "=================================="
echo ""
echo "📚 Documentation Available:"
echo "  - OR_TOOLS_ENHANCEMENT_GUIDE.md (Comprehensive guide)"
echo "  - OR_TOOLS_QUICK_REFERENCE.md (Quick reference)"
echo "  - OR_TOOLS_IMPLEMENTATION_SUMMARY.md (Implementation details)"
echo ""
echo "🚀 Next Steps:"
echo "  1. Restart your backend server:"
echo "     cd backend && uvicorn app.main:app --reload"
echo ""
echo "  2. Navigate to the enhanced optimization page:"
echo "     http://localhost:3000/optimization-enhanced"
echo ""
echo "  3. Read the Quick Reference:"
echo "     cat OR_TOOLS_QUICK_REFERENCE.md"
echo ""
echo "🎯 Quick Test:"
echo "  - Login as admin or finance user"
echo "  - Go to 'Advanced Optimization' in sidebar"
echo "  - Click 'Run Optimization' with CP_SAT solver"
echo "  - Review multiple proposals"
echo ""
echo "Happy Optimizing! 🚀"

