# PDSS Deployment Package Creation Guide

This guide explains how to create deployment packages for the Procurement Decision Support System (PDSS) for both Windows and Linux platforms.

## Quick Start

### Create Packages for Both Platforms (Windows Only)

Run the unified PowerShell script from Windows to create packages for both platforms:

```powershell
cd installation_packages
powershell -ExecutionPolicy Bypass -File create_unified_deployment_packages.ps1
```

This will create:
- **Linux Package**: `pdss-linux-v1.0.0` folder and `pdss-linux-v1.0.0-YYYYMMDDHHMM.zip`
- **Windows Package**: `PDSS_Windows_v1.0.0_YYYYMMDDHHMM` folder and `PDSS_Windows_v1.0.0_YYYYMMDDHHMM.zip`

### Create Windows Package Only

```batch
cd installation_packages
create_windows_deployment_package.bat
```

### Create Linux Package Only (from Windows)

Use the PowerShell script:

```powershell
cd installation_packages
powershell -ExecutionPolicy Bypass -File create_linux_installer_package.ps1
```

## Package Creation Scripts

### 1. Unified Creator (Recommended)

**File**: `create_unified_deployment_packages.ps1`

**Platform**: Windows (PowerShell)

**What it does**:
- Creates deployment packages for BOTH Windows and Linux
- Includes all necessary files and configuration
- Creates proper installers for each platform
- Generates ZIP archives for easy distribution

**Usage**:
```powershell
powershell -ExecutionPolicy Bypass -File create_unified_deployment_packages.ps1
```

### 2. Windows Package Creator

**File**: `create_windows_deployment_package.bat`

**Platform**: Windows (Batch)

**What it does**:
- Creates Windows-only deployment package
- Includes Windows installer (INSTALL.bat)
- Creates management scripts (start.bat, stop.bat, etc.)
- Generates ZIP archive

**Usage**:
```batch
create_windows_deployment_package.bat
```

### 3. Linux Package Creator

**File**: `create_linux_installer_package.ps1`

**Platform**: Windows (PowerShell, creates Linux package)

**What it does**:
- Creates Linux deployment package
- Includes Linux installer (install.sh) with Unix line endings
- Creates management scripts with Unix line endings
- Generates ZIP archive

**Usage**:
```powershell
powershell -ExecutionPolicy Bypass -File create_linux_installer_package.ps1
```

## Package Structure

Both packages contain:

```
Package/
├── INSTALL.bat (Windows) or install.sh (Linux)
├── README.txt
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── [application files]
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── src/
│   └── public/
├── docs/
│   └── [documentation files]
├── scripts/
│   ├── start.bat / start.sh
│   ├── stop.bat / stop.sh
│   ├── status.bat / status.sh
│   └── restart.bat / restart.sh
└── config/
    └── .env.example
```

## Installation Process

### Windows Installation

1. Extract the package to a directory on Windows Server
2. Right-click `INSTALL.bat` and select "Run as Administrator"
3. Wait for installation to complete
4. Access at `http://localhost:3000`

### Linux Installation

1. Transfer the ZIP file to Linux server
2. Extract: `unzip pdss-linux-v1.0.0-YYYYMMDDHHMM.zip`
3. Navigate: `cd pdss-linux-v1.0.0`
4. Make executable: `chmod +x install.sh`
5. Run installer: `sudo ./install.sh`
6. Access at `http://localhost:3000`

## Requirements for Package Creation

### Windows Machine (For Creating Packages)

- Windows 10/11 or Windows Server 2019+
- PowerShell 5.1+ (usually pre-installed)
- Write access to `installation_packages` directory
- Access to parent directory (`..\backend`, `..\frontend`, `..\docker-compose.yml`)

### Target Server Requirements

#### Windows Server
- Windows 10/11 or Windows Server 2019+
- Docker Desktop for Windows
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space

#### Linux Server
- Linux (Ubuntu 18.04+, Debian 10+, CentOS 7+, RHEL 7+)
- Docker Engine 20.10+
- Docker Compose 1.29+
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space

## Package Contents

### Application Files
- Complete backend application (Python/FastAPI)
- Complete frontend application (React/TypeScript)
- Docker configuration files
- Database initialization scripts

### Installation Scripts
- **Windows**: `INSTALL.bat` - Automated installer with administrator checks
- **Linux**: `install.sh` - Automated installer with prerequisite checks

### Management Scripts
Both platforms include:
- **Start**: Start all PDSS services
- **Stop**: Stop all PDSS services
- **Status**: Check service status
- **Restart**: Restart all services

### Configuration
- `.env.example` - Template configuration file
- Production-ready defaults
- Security notes and recommendations

### Documentation
- README files
- System requirements
- Installation instructions
- Default credentials

## Verification

After package creation, verify the package:

### Windows Package
```batch
cd PDSS_Windows_v1.0.0_YYYYMMDDHHMM
VERIFY_PACKAGE.bat
```

### Linux Package
```bash
cd pdss-linux-v1.0.0
chmod +x verify_package.sh
./verify_package.sh
```

## Distribution

### Recommended Distribution Methods

1. **ZIP Archive**: Transfer ZIP file to target server, extract, and install
2. **Network Share**: Copy entire package folder to network share
3. **USB Drive**: Copy package to USB drive for offline installation

### Package Sizes

- **Windows Package**: ~50-100 MB (compressed: ~20-40 MB)
- **Linux Package**: ~50-100 MB (compressed: ~20-40 MB)

*Note: Sizes may vary based on application code and dependencies*

## Troubleshooting

### Package Creation Fails

**Issue**: Script fails with "directory not found"
- **Solution**: Ensure you're running from `installation_packages` directory
- Verify parent directory has `backend`, `frontend`, and `docker-compose.yml`

**Issue**: PowerShell execution policy error
- **Solution**: Run with `-ExecutionPolicy Bypass` flag:
  ```powershell
  powershell -ExecutionPolicy Bypass -File create_unified_deployment_packages.ps1
  ```

### Installation Fails on Target Server

**Issue**: Docker not found
- **Solution**: Install Docker Desktop (Windows) or Docker Engine (Linux) first

**Issue**: Permission denied (Linux)
- **Solution**: Ensure installer has execute permissions: `chmod +x install.sh`

**Issue**: Administrator privileges required (Windows)
- **Solution**: Right-click `INSTALL.bat` and select "Run as Administrator"

## Default Credentials

After installation, use these credentials:

- **Admin**: `admin` / `admin123`
- **Finance**: `finance1` / `finance123`
- **PM**: `pm1` / `pm123`
- **Procurement**: `proc1` / `proc123`

**⚠️ IMPORTANT**: Change all default passwords after first login!

## Support

For issues or questions:
1. Check the documentation in the `docs/` folder of your package
2. Review the README.txt file in the package root
3. Contact your system administrator

## Version History

- **v1.0.0** (2025-01-XX): Initial deployment package creation
  - Unified package creator for both platforms
  - Windows and Linux installers
  - Management scripts for both platforms
  - Complete documentation

