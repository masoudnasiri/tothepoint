# 🔧 Line Endings Issue - FIXED

## ❌ Problem Identified

The original Linux package had **Windows line endings (CRLF)** instead of **Unix line endings (LF)**, causing shell script errors:

```bash
root@vm:~# sudo ./install.sh
: not foundh: 1: #!/bin/bash
: not foundh: 6:
./install.sh: 7: set: Illegal option -
```

**Root Cause:** PowerShell on Windows saves files with CRLF (`\r\n`) by default, but Linux expects LF (`\n`).

---

## ✅ Solutions Provided

### Solution 1: Fix Existing Package (IMMEDIATE)

If you already have the old package on your Linux system, use one of these quick fixes:

#### **Option A: Using dos2unix (Recommended)**
```bash
# Install dos2unix
sudo apt-get install dos2unix   # Ubuntu/Debian
# or
sudo yum install dos2unix       # CentOS/RHEL

# Fix all shell scripts
cd pdss-linux-installer_v1.0.0_*/
find . -name "*.sh" -exec dos2unix {} \;

# Now run installer
sudo ./install.sh
```

#### **Option B: Using sed (No installation needed)**
```bash
cd pdss-linux-installer_v1.0.0_*/
for file in $(find . -name "*.sh"); do 
    sed -i 's/\r$//' "$file"
done
chmod +x install.sh verify_package.sh scripts/*.sh

# Now run installer
sudo ./install.sh
```

#### **Option C: One-liner with tr**
```bash
cd pdss-linux-installer_v1.0.0_*/
for file in $(find . -name "*.sh"); do 
    tr -d '\r' < "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
    chmod +x "$file"
done

# Now run installer
sudo ./install.sh
```

---

### Solution 2: Use New Fixed Package (RECOMMENDED)

**New Package Created:** `pdss-linux_v1.0.0_202510191518.zip`

This package has **proper Unix line endings** and will work immediately on Linux:

```bash
# Download/transfer the new package
unzip pdss-linux_v1.0.0_202510191518.zip

# Navigate to package
cd pdss-linux-installer_v1.0.0_202510191518

# Make installer executable
chmod +x install.sh

# Run installer
sudo ./install.sh
```

**No line ending conversion needed!** ✨

---

## 🔍 What Was Changed

### Updated Package Creator

Modified `create_linux_installer_package.ps1` to convert all shell scripts to Unix line endings:

```powershell
# Before (had CRLF):
$script | Out-File -FilePath "$file.sh" -Encoding UTF8

# After (has LF):
$script -replace "`r`n", "`n" | Out-File -FilePath "$file.sh" -Encoding UTF8
```

### Files Fixed

All shell scripts now have proper Unix line endings:
- ✅ `install.sh`
- ✅ `verify_package.sh`
- ✅ `scripts/start.sh`
- ✅ `scripts/stop.sh`
- ✅ `scripts/status.sh`
- ✅ `scripts/logs.sh`
- ✅ `scripts/restart.sh`
- ✅ `scripts/backup.sh`
- ✅ `scripts/uninstall.sh`

---

## 📦 Package Comparison

| Package | Build Time | Line Endings | Status |
|---------|-----------|--------------|--------|
| **pdss-linux_v1.0.0_202510191456.zip** | 14:56 | ❌ CRLF (Windows) | Requires fix |
| **pdss-linux_v1.0.0_202510191518.zip** | 15:18 | ✅ LF (Unix) | Ready to use |

---

## 🎯 Recommended Action

### For Your Current Installation

Use the **quick fix** on your existing package:

```bash
cd pdss-linux-installer_v1.0.0_202510191456
for file in $(find . -name "*.sh"); do sed -i 's/\r$//' "$file"; done
chmod +x install.sh verify_package.sh scripts/*.sh
sudo ./install.sh
```

### For Future Distributions

Use the **new fixed package**:
```
pdss-linux_v1.0.0_202510191518.zip
```

---

## 📋 Verification

### Check Line Endings

To verify a file has correct line endings:

```bash
# Check for Windows line endings (CRLF)
file install.sh

# Should show:
# Unix:    "Bourne-Again shell script, ASCII text executable"
# Windows: "Bourne-Again shell script, ASCII text executable, with CRLF line terminators"

# Or use od command
od -c install.sh | grep -o '\\r'
# If this returns nothing, line endings are correct (LF only)
# If it returns \r characters, file has CRLF
```

### Test Installation

After fixing line endings:

```bash
# Should work without errors
sudo ./install.sh

# Expected output:
# ============================================================================
#   PDSS Linux Installer
# ============================================================================
# [1/9] Checking prerequisites...
# ...
```

---

## 🔧 Technical Details

### Why This Happened

1. **PowerShell on Windows** saves text files with CRLF (`\r\n`) by default
2. **Linux shell** expects LF (`\n`) only
3. The carriage return (`\r`) causes parsing errors

### How It Was Fixed

1. Updated PowerShell script to use `-replace "`r`n", "`n"`
2. This converts CRLF to LF before writing files
3. New packages have proper Unix line endings

### Prevention

Future packages created with the updated script will automatically have correct line endings.

---

## 📚 Additional Resources

**Quick Fix Guide:** `FIX_LINE_ENDINGS.md`  
**Package Creator Guide:** `PACKAGE_CREATORS_GUIDE.md`  
**Installation Guide:** `INSTALLATION_GUIDE.md`

---

## 🎊 Summary

### Issue
- Original Linux package had Windows line endings (CRLF)
- Caused shell script parsing errors on Linux

### Fix Applied
✅ Updated package creator to use Unix line endings (LF)  
✅ Generated new fixed package: `pdss-linux_v1.0.0_202510191518.zip`  
✅ Provided quick fix for existing packages  
✅ Created documentation for troubleshooting  

### Current Status
- ✅ **Problem identified**
- ✅ **Root cause fixed**
- ✅ **New package generated**
- ✅ **Quick fix provided**
- ✅ **Documentation updated**

---

## 🚀 Next Steps

### Option 1: Use Quick Fix on Current Package
```bash
cd pdss-linux-installer_v1.0.0_202510191456
for file in $(find . -name "*.sh"); do sed -i 's/\r$//' "$file"; done
chmod +x install.sh verify_package.sh scripts/*.sh
sudo ./install.sh
```

### Option 2: Download New Fixed Package
```bash
# Transfer: pdss-linux_v1.0.0_202510191518.zip
unzip pdss-linux_v1.0.0_202510191518.zip
cd pdss-linux-installer_v1.0.0_202510191518
chmod +x install.sh
sudo ./install.sh
```

---

**Status:** ✅ **ISSUE RESOLVED**

**Fixed Package:** `pdss-linux_v1.0.0_202510191518.zip`  
**Created:** October 19, 2025, 15:18  
**Line Endings:** Unix (LF) ✓

---

**You can now install PDSS on Linux without line ending issues!** 🎉

