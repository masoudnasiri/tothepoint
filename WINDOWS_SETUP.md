# Windows Setup Guide for Procurement DSS

This guide will help you set up and run the Procurement DSS system on Windows.

## Prerequisites

### 1. Docker Desktop for Windows
Download and install Docker Desktop from: https://www.docker.com/products/docker-desktop

**System Requirements:**
- Windows 10 64-bit: Pro, Enterprise, or Education (Build 19041 and higher)
- OR Windows 11 64-bit: Home or Pro (Build 22000 and higher)
- WSL 2 feature enabled
- Virtualization enabled in BIOS
- At least 4GB RAM available for Docker

### 2. Enable WSL 2 (if not already enabled)
1. Open PowerShell as Administrator
2. Run: `dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart`
3. Run: `dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart`
4. Restart your computer
5. Download and install the WSL2 Linux kernel update package
6. Set WSL 2 as default: `wsl --set-default-version 2`

## Quick Setup

### Step 1: Download/Clone the Project
```cmd
git clone <repository-url>
cd cahs_flow_project
```

### Step 2: Run Setup Script
Double-click `setup-windows.bat` or run:
```cmd
setup-windows.bat
```

This script will:
- Check if Docker Desktop is installed
- Verify Docker is running
- Check if required ports are available
- Confirm your system is ready

### Step 3: Start the System
Double-click `start.bat` or run:
```cmd
start.bat
```

The system will:
- Stop any existing containers
- Build the Docker images
- Start all services (database, backend, frontend)
- Display access URLs and login credentials

### Step 4: Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Available Scripts

| Script | Purpose |
|--------|---------|
| `setup-windows.bat` | Check system requirements and setup |
| `start.bat` | Start the Procurement DSS system |
| `stop.bat` | Stop the system |
| `logs.bat` | View system logs |
| `reset.bat` | Reset system (remove all data) |

## Default Login Credentials

**⚠️  IMPORTANT SECURITY NOTICE:**

The system includes pre-configured users. You **MUST** change all passwords immediately after first login.

| Role | Username | Action Required |
|------|----------|-----------------|
| Admin | admin | ⚠️ Change password immediately |
| Project Manager | pm1 | ⚠️ Change password immediately |
| Procurement Specialist | proc1 | ⚠️ Change password immediately |
| Finance User | finance1 | ⚠️ Change password immediately |

## Troubleshooting

### Docker Desktop Issues

**Docker Desktop won't start:**
1. Ensure virtualization is enabled in BIOS
2. Check if Hyper-V is enabled (Windows Features)
3. Restart Docker Desktop
4. Try running as Administrator

**"Docker is not running" error:**
1. Start Docker Desktop from Start menu
2. Wait for the green icon in system tray
3. Check Docker Desktop status in Settings

### Port Conflicts

**Error: Port already in use**
1. Check what's using the port:
   ```cmd
   netstat -ano | findstr :3000
   netstat -ano | findstr :8000
   netstat -ano | findstr :5432
   ```
2. Stop the conflicting service or change ports in `docker-compose.yml`

### System Performance

**Slow startup or performance issues:**
1. Allocate more RAM to Docker Desktop (Settings > Resources > Advanced)
2. Close unnecessary applications
3. Ensure SSD storage for better performance
4. Disable Windows Defender real-time protection for project folder (temporarily)

### Database Connection Issues

**Backend can't connect to database:**
1. Wait longer for PostgreSQL to start (up to 2 minutes)
2. Check logs: `logs.bat`
3. Restart the system: `stop.bat` then `start.bat`

### Frontend Not Loading

**Frontend shows connection error:**
1. Check if backend is running: http://localhost:8000/docs
2. Verify Docker containers are running:
   ```cmd
   docker-compose ps
   ```
3. Check logs for errors: `logs.bat`

## Manual Commands

If the batch files don't work, you can run commands manually:

```cmd
# Check Docker status
docker --version
docker-compose --version

# Start the system
docker-compose up --build -d

# Stop the system
docker-compose down

# View logs
docker-compose logs -f

# Reset everything
docker-compose down -v
```

## Windows-Specific Notes

### File Paths
- Use forward slashes (/) in docker-compose.yml (Docker handles this)
- Avoid spaces in project folder path
- Use short folder names to avoid Windows path length limits

### Antivirus Software
- Add project folder to antivirus exclusions
- Docker Desktop may be flagged - add to exclusions
- Real-time scanning can slow down Docker operations

### Windows Defender
- May interfere with Docker containers
- Consider adding exclusions for:
  - Docker Desktop installation folder
  - Project folder
  - Docker data directory (usually `%USERPROFILE%\AppData\Local\Docker`)

### PowerShell Execution Policy
If you get execution policy errors:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Development on Windows

### Using Windows Subsystem for Linux (WSL)
For better performance, you can run Docker from WSL2:

1. Install WSL2 with Ubuntu
2. Install Docker Desktop with WSL2 backend enabled
3. Clone project in WSL2 filesystem (`\\wsl$\Ubuntu\home\username\`)
4. Use WSL2 terminal for running commands

### Using Git Bash
You can also use Git Bash instead of Command Prompt:
```bash
# In Git Bash
./start.sh
./stop.sh
```

## Getting Help

### Check System Status
```cmd
# Docker status
docker info

# Container status
docker-compose ps

# Service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
```

### Common Solutions
1. **Restart Docker Desktop** - Solves most issues
2. **Restart Windows** - If Docker won't start
3. **Check Windows updates** - Ensure latest updates installed
4. **Disable VPN/Proxy** - May interfere with Docker networking
5. **Run as Administrator** - If permission issues occur

### Performance Tips
1. Close unnecessary browser tabs and applications
2. Allocate at least 4GB RAM to Docker Desktop
3. Use SSD storage for better I/O performance
4. Enable hardware virtualization in BIOS
5. Keep Docker Desktop updated

## Next Steps

Once the system is running:
1. Login with admin credentials
2. Create additional users as needed
3. Set up projects and items
4. Configure procurement options
5. Set budget constraints
6. Run optimization

For detailed usage instructions, see the main README.md file.
