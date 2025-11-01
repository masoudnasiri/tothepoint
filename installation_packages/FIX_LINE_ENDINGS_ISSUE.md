# Fix for Linux Install Script Line Endings Issue

## Problem

The Linux install script (`install.sh`) was created with Windows line endings (CRLF), causing errors:
- `#!/bin/bash: not found` - Shebang line not recognized
- `-e` being printed instead of color codes
- Script execution failures

## Solution

The package creator has been fixed to generate scripts with proper Unix line endings (LF only).

## For Existing Packages

If you have an existing package with this issue, run these commands on your Linux server:

```bash
# Option 1: Use dos2unix (if available)
sudo apt-get install dos2unix -y  # Ubuntu/Debian
sudo yum install dos2unix -y      # CentOS/RHEL
dos2unix install.sh
chmod +x install.sh

# Option 2: Use sed (built-in)
sed -i 's/\r$//' install.sh
chmod +x install.sh

# Option 3: Use tr
tr -d '\r' < install.sh > install_fixed.sh
mv install_fixed.sh install.sh
chmod +x install.sh
```

Then run the installer:
```bash
sudo ./install.sh
```

## For New Packages

The updated `create_unified_deployment_packages.ps1` script now:
- Uses `printf` instead of `echo -e` for better compatibility
- Uses `>/dev/null 2>&1` instead of `&>/dev/null`
- Writes files with UTF8NoBOM encoding and LF-only line endings
- Properly handles all shell script redirections

## Verification

After fixing or creating a new package, verify the line endings:
```bash
file install.sh
# Should show: install.sh: Bourne-Again shell script, ASCII text executable
# NOT: install.sh: Bourne-Again shell script, ASCII text executable, with CRLF line terminators
```

Or check manually:
```bash
hexdump -C install.sh | head -1
# Should NOT show "0d 0a" (CRLF), only "0a" (LF)
```

