# 🔧 Fix Line Endings Issue

## Problem

Linux scripts created on Windows have Windows line endings (CRLF) which causes errors like:
```
: not foundh: 1: #!/bin/bash
set: Illegal option -
```

## Quick Fix

### Option 1: Using dos2unix (Recommended)

```bash
# Install dos2unix if not present
sudo apt-get install dos2unix   # Ubuntu/Debian
# or
sudo yum install dos2unix       # CentOS/RHEL

# Fix all shell scripts in package
cd pdss-linux-installer_v1.0.0_*/
find . -name "*.sh" -exec dos2unix {} \;

# Now run installer
sudo ./install.sh
```

### Option 2: Using sed

```bash
# Fix install.sh
cd pdss-linux-installer_v1.0.0_*/
sed -i 's/\r$//' install.sh
sed -i 's/\r$//' verify_package.sh
find scripts/ -name "*.sh" -exec sed -i 's/\r$//' {} \;

# Now run installer
sudo ./install.sh
```

### Option 3: Using tr

```bash
# Fix install.sh
cd pdss-linux-installer_v1.0.0_*/
tr -d '\r' < install.sh > install_fixed.sh
mv install_fixed.sh install.sh
chmod +x install.sh

# Fix verify script
tr -d '\r' < verify_package.sh > verify_fixed.sh
mv verify_fixed.sh verify_package.sh
chmod +x verify_package.sh

# Fix management scripts
for script in scripts/*.sh; do
    tr -d '\r' < "$script" > "${script}.tmp"
    mv "${script}.tmp" "$script"
    chmod +x "$script"
done

# Now run installer
sudo ./install.sh
```

### Option 4: One-liner Fix All Scripts

```bash
cd pdss-linux-installer_v1.0.0_*/
for file in $(find . -name "*.sh"); do sed -i 's/\r$//' "$file"; done
chmod +x install.sh verify_package.sh scripts/*.sh
sudo ./install.sh
```

## After Fix

The installer should work normally:
```bash
sudo ./install.sh
```

## Prevention

Future packages will be created with correct line endings automatically.

