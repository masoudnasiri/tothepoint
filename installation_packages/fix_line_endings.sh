#!/bin/bash
# Fix line endings for Linux shell scripts
# This script converts CRLF to LF for all .sh files

find . -name "*.sh" -type f -exec dos2unix {} \; 2>/dev/null || {
    # If dos2unix is not available, use sed
    find . -name "*.sh" -type f -exec sed -i 's/\r$//' {} \;
}

echo "Line endings fixed for all .sh files"

